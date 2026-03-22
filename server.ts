import express from "express";
import { createServer as createViteServer } from "vite";
import { exec, spawn } from "child_process";
import path from "path";
import fs from "fs";
import cors from "cors";
import { createServer } from "http";
import { Server } from "socket.io";
import { Storage } from "@google-cloud/storage";
import { glob } from "glob";

async function startServer() {
  const app = express();
  const httpServer = createServer(app);
  const io = new Server(httpServer, {
    cors: {
      origin: "*",
      methods: ["GET", "POST"]
    }
  });
  const PORT = 3000;

  const storage = process.env.GCS_BUCKET_NAME ? new Storage() : null;
  const bucketName = process.env.GCS_BUCKET_NAME;

  app.use(cors());
  app.use(express.json());

  // Download state tracking
  const downloads: Record<string, {
    id: string;
    status: 'Pending' | 'Downloading' | 'Completed' | 'Failed';
    progress: number;
    speed: string;
    error?: string;
    startTime?: number;
    totalSize?: string;
    eta?: string;
  }> = {};

  // Serve outputs directory
  const outputsDir = path.join(process.cwd(), "outputs");
  if (!fs.existsSync(outputsDir)) {
    fs.mkdirSync(outputsDir, { recursive: true });
  }
  app.use("/outputs", express.static(outputsDir));

  // API Routes
  app.get("/api/datasets", (req, res) => {
    exec("(python3 backend/get_datasets.py || python backend/get_datasets.py)", (error, stdout, stderr) => {
      if (error) {
        console.error(`Error: ${error.message}`);
        return res.status(500).json({ error: error.message, stderr });
      }
      try {
        const datasets = JSON.parse(stdout.trim());
        res.json(datasets);
      } catch (e) {
        res.status(500).json({ error: "Failed to parse datasets", stdout });
      }
    });
  });

  app.post("/api/gcs/upload", async (req, res) => {
    if (!storage || !bucketName) {
      return res.status(500).json({ error: "GCS not configured" });
    }
    const { filePath, destination } = req.body;
    try {
      await storage.bucket(bucketName).upload(filePath, { destination });
      res.json({ status: "success" });
    } catch (error) {
      res.status(500).json({ error: (error as Error).message });
    }
  });

  app.get("/api/kaggle/download/status", (req, res) => {
    res.json(Object.values(downloads));
  });

  app.post("/api/kaggle/download", (req, res) => {
    const { datasetId, totalSize = "Unknown" } = req.body;
    if (!datasetId) {
      return res.status(400).json({ error: "datasetId is required" });
    }

    if (downloads[datasetId] && downloads[datasetId].status === 'Downloading') {
      return res.json({ status: "already_downloading", datasetId });
    }

    downloads[datasetId] = {
      id: datasetId,
      status: 'Pending',
      progress: 0,
      speed: "0 KB/s",
      startTime: Date.now(),
      totalSize
    };

    io.emit('download:status', downloads[datasetId]);

    // Start download in background
    processDownload(datasetId);

    res.json({ status: "queued", datasetId });
  });

  async function processDownload(datasetId: string) {
    const download = downloads[datasetId];
    download.status = 'Downloading';
    io.emit('download:status', download);

    const datasetsDir = path.join(process.cwd(), "datasets");
    if (!fs.existsSync(datasetsDir)) {
      fs.mkdirSync(datasetsDir, { recursive: true });
    }

    // Simulate progress for now as kagglehub doesn't expose it easily via CLI
    // In a real scenario, we'd pipe the output of a python script that uses kaggle API with a progress callback
    let progress = 0;
    const parseSize = (sizeStr: string): number => {
      const units: Record<string, number> = { 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4 };
      const match = sizeStr?.match(/^([\d.]+)\s*([A-Z]+)$/i);
      if (!match) return 0;
      const value = parseFloat(match[1]);
      const unit = match[2].toUpperCase();
      return value * (units[unit] || 1);
    };

    const totalBytes = parseSize(download.totalSize || "0 MB");

    const interval = setInterval(() => {
      if (progress < 95) {
        const currentSpeedMBs = Math.random() * 5 + 1;
        progress += (currentSpeedMBs / (totalBytes / (1024 * 1024) || 100)) * 100;
        download.progress = Math.min(progress, 95);
        download.speed = `${currentSpeedMBs.toFixed(1)} MB/s`;
        
        if (totalBytes > 0) {
          const remainingBytes = totalBytes * (1 - download.progress / 100);
          const remainingSeconds = remainingBytes / (currentSpeedMBs * 1024 * 1024);
          if (remainingSeconds > 0) {
            const mins = Math.floor(remainingSeconds / 60);
            const secs = Math.floor(remainingSeconds % 60);
            download.eta = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
          } else {
            download.eta = "0s";
          }
        } else {
          download.eta = "Calculating...";
        }

        io.emit('download:status', download);
      }
    }, 1000);

    const downloadScript = `
import os
import sys
import shutil
import kagglehub

try:
    path = kagglehub.dataset_download("${datasetId}")
    target_dir = os.path.join("${datasetsDir}", "${datasetId.replace("/", "_")}")
    os.makedirs(target_dir, exist_ok=True)
    
    if os.path.isdir(path):
        for item in os.listdir(path):
            s = os.path.join(path, item)
            d = os.path.join(target_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
    else:
        shutil.copy2(path, target_dir)
    print(f"SUCCESS:{target_dir}")
except Exception as e:
    print(f"ERROR:{str(e)}")
`;

    const scriptPath = path.join(process.cwd(), `temp_download_${Math.random().toString(36).substring(7)}.py`);
    fs.writeFileSync(scriptPath, downloadScript);

    exec(`(python3 ${scriptPath} || python ${scriptPath})`, async (error, stdout, stderr) => {
      clearInterval(interval);
      if (fs.existsSync(scriptPath)) fs.unlinkSync(scriptPath);

      if (error || stdout.includes("ERROR:")) {
        download.status = 'Failed';
        download.error = error?.message || stdout.split("ERROR:")[1]?.trim() || "Unknown error";
        io.emit('download:status', download);
      } else {
        const targetDir = stdout.split("SUCCESS:")[1]?.trim();
        if (targetDir && storage && bucketName) {
            try {
                const files = await glob(`${targetDir}/**/*`, { nodir: true });
                for (const file of files) {
                    const relativePath = path.relative(targetDir, file);
                    await storage.bucket(bucketName).upload(file, {
                        destination: `datasets/${datasetId.replace(/\//g, '_')}/${relativePath}`
                    });
                }
            } catch (e) {
                console.error("GCS upload failed:", e);
            }
        }
        download.status = 'Completed';
        download.progress = 100;
        download.speed = "0 KB/s";
        io.emit('download:status', download);
      }
    });
  }

  app.post("/api/kaggle/download/retry", (req, res) => {
    const { datasetId } = req.body;
    if (!datasetId || !downloads[datasetId]) {
      return res.status(404).json({ error: "Download not found" });
    }
    processDownload(datasetId);
    res.json({ status: "retrying", datasetId });
  });

  app.post("/api/kaggle/activate", (req, res) => {
    const { datasetId } = req.body;
    if (!datasetId) {
      return res.status(400).json({ error: "datasetId is required" });
    }

    const datasetDir = path.join(process.cwd(), "datasets", datasetId.replace("/", "_"));
    if (!fs.existsSync(datasetDir)) {
      return res.status(404).json({ error: "Dataset not found on disk" });
    }

    console.log(`Activating dataset: ${datasetId}...`);
    
    // We need to find where the actual images are within the dataset
    // Some datasets have nested folders. We'll look for folders containing images.
    const findImageDir = (dir: string): string | null => {
      const files = fs.readdirSync(dir);
      const hasImages = files.some(f => f.match(/\.(jpg|jpeg|png)$/i));
      if (hasImages) return dir;
      
      for (const file of files) {
        const fullPath = path.join(dir, file);
        if (fs.statSync(fullPath).isDirectory()) {
          const found = findImageDir(fullPath);
          if (found) return found;
        }
      }
      return null;
    };

    const imageSourceDir = findImageDir(datasetDir);
    if (!imageSourceDir) {
      return res.status(400).json({ error: "No images found in dataset" });
    }

    // Run split.py
    const splitCmd = `python3 split.py --input-dir "${imageSourceDir}" --output-dir "${path.join(process.cwd(), "data", datasetId.replace("/", "_"))}"`;
    
    exec(splitCmd, (error, stdout, stderr) => {
      if (error) {
        console.error(`Error splitting dataset: ${error.message}`);
        return res.status(500).json({ error: "Failed to split dataset", details: stderr || error.message });
      }
      console.log(`Split output: ${stdout}`);
      res.json({ status: "activated" });
    });
  });

  app.get("/api/metrics", (req, res) => {
    const metricsPath = path.join(outputsDir, "metrics.json");
    if (fs.existsSync(metricsPath)) {
      try {
        const metrics = JSON.parse(fs.readFileSync(metricsPath, "utf-8"));
        res.json(metrics);
      } catch (e) {
        res.status(500).json({ error: "Failed to parse metrics" });
      }
    } else {
      res.status(404).json({ error: "Metrics not found" });
    }
  });

  app.get("/api/data/check", (req, res) => {
    const dataDir = path.join(process.cwd(), "data");
    res.json({ exists: fs.existsSync(dataDir) });
  });

  app.get("/api/dataset/preview", (req, res) => {
    const dataDir = path.join(process.cwd(), "data", "train");
    if (!fs.existsSync(dataDir)) {
      return res.json({ classes: [], totalImages: 0, samples: [] });
    }

    try {
      const classes = fs.readdirSync(dataDir).filter(f => fs.statSync(path.join(dataDir, f)).isDirectory());
      let totalImages = 0;
      const samples: any[] = [];

      classes.forEach(cls => {
        const clsDir = path.join(dataDir, cls);
        const files = fs.readdirSync(clsDir).filter(f => f.match(/\.(jpg|jpeg|png)$/i));
        totalImages += files.length;
        
        // Take up to 5 samples per class
        files.slice(0, 5).forEach(file => {
          samples.push({
            imageName: file,
            class: cls,
            previewUrl: `/api/data/train/${cls}/${file}`,
            filePath: `/data/train/${cls}/${file}`
          });
        });
      });

      res.json({ classes, totalImages, samples });
    } catch (e) {
      res.status(500).json({ error: "Failed to read dataset preview" });
    }
  });

  app.use("/api/data", express.static(path.join(process.cwd(), "data")));

  app.get("/api/kaggle/config", (req, res) => {
    const kaggleDir = path.join(process.env.HOME || "/root", ".kaggle");
    const configPath = path.join(kaggleDir, "kaggle.json");
    
    // Check environment variables first (injected by AI Studio if configured)
    const envUsername = process.env.KAGGLE_USERNAME;
    const envKey = process.env.KAGGLE_KEY;

    if (envUsername && envKey) {
      return res.json({ username: envUsername, key: envKey });
    }

    if (fs.existsSync(configPath)) {
      try {
        const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
        res.json({ username: config.username, key: config.key });
      } catch (e) {
        res.status(500).json({ error: "Failed to parse Kaggle config" });
      }
    } else {
      res.status(404).json({ error: "Kaggle config not found" });
    }
  });

  app.post("/api/kaggle/config", (req, res) => {
    const { username, key } = req.body;
    if (!username || !key) {
      return res.status(400).json({ error: "Username and key are required" });
    }
    
    const kaggleDir = path.join(process.env.HOME || "/root", ".kaggle");
    if (!fs.existsSync(kaggleDir)) {
      fs.mkdirSync(kaggleDir, { recursive: true });
    }
    
    const configPath = path.join(kaggleDir, "kaggle.json");
    try {
      fs.writeFileSync(configPath, JSON.stringify({ username, key }));
      fs.chmodSync(configPath, 0o600);
      res.json({ status: "success", message: "Kaggle configuration saved" });
    } catch (e) {
      res.status(500).json({ error: "Failed to save Kaggle config" });
    }
  });

  app.delete("/api/kaggle/config", (req, res) => {
    const kaggleDir = path.join(process.env.HOME || "/root", ".kaggle");
    const configPath = path.join(kaggleDir, "kaggle.json");
    
    if (fs.existsSync(configPath)) {
      try {
        fs.unlinkSync(configPath);
        res.json({ status: "success", message: "Kaggle configuration cleared" });
      } catch (e) {
        res.status(500).json({ error: "Failed to delete Kaggle config" });
      }
    } else {
      res.status(404).json({ error: "Kaggle configuration not found" });
    }
  });

  app.get("/api/admin/check-python", (req, res) => {
    console.log("Checking Python environment status...");
    const cmd = `(python3 -m pip list || pip3 list || python -m pip list || pip list || echo "Pip not found")`;
    exec(cmd, (error, stdout, stderr) => {
      res.json({ stdout, stderr, error: error?.message });
    });
  });

  app.get("/api/admin/install-python", (req, res) => {
    console.log("Manual trigger: Installing Python dependencies...");
    const installCmd = (pkg: string) => `(python3 -m pip install --no-cache-dir --prefer-binary ${pkg} || pip3 install --no-cache-dir --prefer-binary ${pkg} || python -m pip install --no-cache-dir --prefer-binary ${pkg} || pip install --no-cache-dir --prefer-binary ${pkg} || python3 -m pip install --user --no-cache-dir --prefer-binary ${pkg} || pip3 install --user --no-cache-dir --prefer-binary ${pkg} || python3 -m pip install --break-system-packages --no-cache-dir --prefer-binary ${pkg} || pip3 install --break-system-packages --no-cache-dir --prefer-binary ${pkg})`;
    const bulkCmd = `(python3 -m pip install --no-cache-dir --prefer-binary -r requirements.txt || pip3 install --no-cache-dir --prefer-binary -r requirements.txt || python -m pip install --no-cache-dir --prefer-binary -r requirements.txt || pip install --no-cache-dir --prefer-binary -r requirements.txt || python3 -m pip install --user --no-cache-dir --prefer-binary -r requirements.txt || pip3 install --user --no-cache-dir --prefer-binary -r requirements.txt || python3 -m pip install --break-system-packages --no-cache-dir --prefer-binary -r requirements.txt || pip3 install --break-system-packages --no-cache-dir --prefer-binary -r requirements.txt)`;

    const runInstall = () => {
      exec(bulkCmd, (error, stdout, stderr) => {
        if (error) {
          console.error(`Error: ${error.message}`);
          
          if (stderr.includes("No module named pip") || stderr.includes("not found")) {
            console.log("Pip missing. Attempting manual pip install...");
            exec("curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && (python3 get-pip.py --user || python get-pip.py --user)", (pipErr) => {
              if (pipErr) return res.status(500).json({ error: "Failed to install pip", details: pipErr.message });
              runInstall();
            });
            return;
          }

          // Try individual install
          try {
            const packages = fs.readFileSync('requirements.txt', 'utf8').split('\n').filter(p => p.trim() && !p.startsWith('--'));
            packages.forEach(pkg => {
              exec(installCmd(pkg), (err) => {
                if (err) console.error(`Failed to install ${pkg}: ${err.message}`);
              });
            });
          } catch (e) {}
          return res.status(500).json({ error: error.message, stderr, message: "Bulk install failed, attempted individual install" });
        }
        res.json({ status: "success", stdout, stderr });
      });
    };

    runInstall();
  });

  app.get("/api/kaggle/search", (req, res) => {
    const { query = "" } = req.query;
    console.log(`Searching Kaggle for: ${query}...`);
    const cmd = `(python3 kaggle_search.py --query "${query}" || python kaggle_search.py --query "${query}")`;
    exec(cmd, (error, stdout, stderr) => {
      if (error) {
        console.error(`Error: ${error.message}`);
        return res.status(500).json({ error: error.message, stderr });
      }
      try {
        const results = JSON.parse(stdout.trim());
        res.json(results);
      } catch (e) {
        res.status(500).json({ error: "Failed to parse search results", stdout });
      }
    });
  });

  app.post("/api/kaggle/download", (req, res) => {
    const { datasetId } = req.body;
    if (!datasetId) {
      return res.status(400).json({ error: "datasetId is required" });
    }
    console.log(`Downloading Kaggle dataset: ${datasetId}...`);
    
    // Ensure datasets directory exists
    const datasetsDir = path.join(process.cwd(), "datasets");
    if (!fs.existsSync(datasetsDir)) {
      fs.mkdirSync(datasetsDir, { recursive: true });
    }

    const downloadScript = `
import os
import sys
import subprocess

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user", "--no-cache-dir"])
    except Exception as e:
        print(f"FAILED_INSTALL:{package}:{str(e)}")

try:
    import kagglehub
except ImportError:
    print("Kagglehub missing, attempting self-install...")
    install_package("kagglehub")
    try:
        import kagglehub
    except ImportError:
        print("ERROR:Could not install kagglehub")
        sys.exit(1)

import shutil
import zipfile

try:
    # Download to a specific directory
    # kagglehub.dataset_download returns the path to the downloaded folder
    path = kagglehub.dataset_download("${datasetId}")
    
    # Define target directory in our app
    target_dir = os.path.join("${datasetsDir}", "${datasetId.replace("/", "_")}")
    os.makedirs(target_dir, exist_ok=True)
    
    # Copy files to our local datasets directory if they aren't already there
    if os.path.isdir(path):
        for item in os.listdir(path):
            s = os.path.join(path, item)
            d = os.path.join(target_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
    else:
        shutil.copy2(path, target_dir)
        
    print(f"DOWNLOAD_PATH:{target_dir}")
except Exception as e:
    print(f"ERROR:{str(e)}")
`;
    const scriptPath = path.join(process.cwd(), "temp_download.py");
    fs.writeFileSync(scriptPath, downloadScript);

    exec(`(python3 ${scriptPath} || python ${scriptPath})`, (error, stdout, stderr) => {
      if (fs.existsSync(scriptPath)) fs.unlinkSync(scriptPath);
      if (error) {
        console.error(`Error: ${error.message}`);
        return res.status(500).json({ error: error.message, stderr });
      }
      console.log(`Stdout: ${stdout}`);
      if (stdout.includes("DOWNLOAD_PATH:")) {
        const downloadPath = stdout.split("DOWNLOAD_PATH:")[1].trim();
        res.json({ status: "complete", path: downloadPath });
      } else {
        res.status(500).json({ error: "Download failed", stdout });
      }
    });
  });

  app.get("/api/kaggle/zip/:datasetId", (req, res) => {
    const { datasetId } = req.params;
    
    // Simulate zipping delay
    setTimeout(() => {
      res.setHeader('Content-Type', 'application/zip');
      res.setHeader('Content-Disposition', `attachment; filename=${datasetId.replace(/\//g, '_')}.zip`);
      // Sending a dummy buffer as a placeholder for the ZIP
      res.send(Buffer.from("PK\x03\x04...DUMMY_ZIP_CONTENT..."));
    }, 1000);
  });

  app.post("/api/evaluate", (req, res) => {
    console.log("Starting evaluation...");
    exec("(python3 evaluate.py || python evaluate.py)", (error, stdout, stderr) => {
      if (error) {
        console.error(`Error: ${error.message}`);
        return res.status(500).json({ error: error.message, stderr });
      }
      console.log(`Stdout: ${stdout}`);
      
      const metricsPath = path.join(outputsDir, "metrics.json");
      if (fs.existsSync(metricsPath)) {
        try {
          const metrics = JSON.parse(fs.readFileSync(metricsPath, "utf-8"));
          res.json(metrics);
        } catch (e) {
          res.status(500).json({ error: "Failed to parse metrics" });
        }
      } else {
        res.json({ status: "complete", stdout });
      }
    });
  });

  app.post("/api/train", (req, res) => {
    const { epochs = 5, modelName = 'fastvit-t12' } = req.body;
    const dataDir = path.join(process.cwd(), "data");
    
    if (!fs.existsSync(dataDir)) {
      return res.status(400).json({ error: `Data directory not found at ${dataDir}. Please run the data acquisition pipeline first.` });
    }

    console.log(`Starting training for ${epochs} epochs using ${modelName}...`);
    
    const trainCmd = modelName === 'fastvit-t12' ? 'python3' : 'python';
    const trainArgs = modelName === 'fastvit-t12' 
      ? ['backend/train_fastvit_t12.py', '--epochs', epochs.toString(), '--data-dir', dataDir]
      : ['train.py', '--epochs', epochs.toString()];

    const trainingProcess = spawn(trainCmd, trainArgs);

    trainingProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log(`Training: ${output}`);
      
      // Parse progress: Epoch [X/Y]
      const match = output.match(/Epoch \[(\d+)\/(\d+)\]/);
      if (match) {
        const currentEpoch = parseInt(match[1]);
        const totalEpochs = parseInt(match[2]);
        const progress = Math.round((currentEpoch / totalEpochs) * 100);
        io.emit('training:status', { status: 'Training', progress, epoch: currentEpoch, totalEpochs });
      }
    });

    trainingProcess.stderr.on('data', (data) => {
      console.error(`Training Error: ${data}`);
    });

    trainingProcess.on('close', (code) => {
      if (code === 0) {
        io.emit('training:status', { status: 'Completed', progress: 100 });
      } else {
        io.emit('training:status', { status: 'Failed', error: `Process exited with code ${code}` });
      }
    });

    res.json({ status: "started" });
  });

  app.post("/api/predict", (req, res) => {
    const { imagePath } = req.body;
    if (!imagePath) {
      return res.status(400).json({ error: "imagePath is required" });
    }
    console.log(`Running inference on ${imagePath}...`);
    exec(`(python3 inference.py --image ${imagePath} || python inference.py --image ${imagePath})`, (error, stdout, stderr) => {
      if (error) {
        console.error(`Error: ${error.message}`);
        return res.status(500).json({ error: error.message, stderr });
      }
      console.log(`Stdout: ${stdout}`);
      try {
        // inference.py should print JSON
        const result = JSON.parse(stdout.split("\n").filter(line => line.trim().startsWith("{")).pop() || "{}");
        res.json(result);
      } catch (e) {
        res.json({ status: "complete", stdout });
      }
    });
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  httpServer.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
    // Install Python dependencies on startup
    console.log("Checking Python environment...");
    
    exec("python3 --version || python --version", (pyVerErr, pyVerOut) => {
      console.log(`Python version: ${pyVerOut || 'Not found'}`);
      
      const installCmd = (pkg: string) => {
        return `(python3 -m pip install --no-cache-dir --prefer-binary ${pkg} || pip3 install --no-cache-dir --prefer-binary ${pkg} || python -m pip install --no-cache-dir --prefer-binary ${pkg} || pip install --no-cache-dir --prefer-binary ${pkg} || python3 -m pip install --user --no-cache-dir --prefer-binary ${pkg} || pip3 install --user --no-cache-dir --prefer-binary ${pkg} || python3 -m pip install --break-system-packages --no-cache-dir --prefer-binary ${pkg} || pip3 install --break-system-packages --no-cache-dir --prefer-binary ${pkg})`;
      };

      const installFromRequirements = () => {
        const cmd = `(python3 -m pip install --no-cache-dir --prefer-binary -r requirements.txt || pip3 install --no-cache-dir --prefer-binary -r requirements.txt || python -m pip install --no-cache-dir --prefer-binary -r requirements.txt || pip install --no-cache-dir --prefer-binary -r requirements.txt || python3 -m pip install --user --no-cache-dir --prefer-binary -r requirements.txt || pip3 install --user --no-cache-dir --prefer-binary -r requirements.txt || python3 -m pip install --break-system-packages --no-cache-dir --prefer-binary -r requirements.txt || pip3 install --break-system-packages --no-cache-dir --prefer-binary -r requirements.txt)`;
        exec(cmd, (error, stdout, stderr) => {
          if (error) {
            console.error(`Error installing Python dependencies: ${error.message}`);
            
            if (stderr.includes("No module named pip") || stderr.includes("not found")) {
              console.log("Pip missing. Attempting manual pip install...");
              exec("curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && (python3 get-pip.py --user || python get-pip.py --user)", (pipInstallErr) => {
                if (!pipInstallErr) installFromRequirements();
              });
              return;
            }

            try {
              const packages = fs.readFileSync('requirements.txt', 'utf8').split('\n').filter(p => p.trim() && !p.startsWith('--'));
              packages.forEach(pkg => {
                exec(installCmd(pkg), (err) => {
                  if (!err) console.log(`Successfully installed ${pkg}`);
                });
              });
            } catch (e) {}
          } else {
            console.log("Python dependencies installed successfully");
          }
        });
      };

      installFromRequirements();
    });
  });
}

startServer();

import React, { useState, useEffect } from 'react';
import { User, Lock, Eye, EyeOff, Image as ImageIcon, ShieldCheck, Badge, Mail, Camera } from 'lucide-react';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword, signInWithPopup, GoogleAuthProvider } from 'firebase/auth';
import { doc, setDoc, getDoc } from 'firebase/firestore';
import { auth, db } from './services/firebase';

export default function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [name, setName] = useState('');
  const [medId, setMedId] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  
  // Captcha state
  const [captchaString, setCaptchaString] = useState('');
  const [captchaInput, setCaptchaInput] = useState('');
  
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);

  const generateCaptcha = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'; // Excluded confusing chars like I, l, 1, O, 0
    let result = '';
    for (let i = 0; i < 6; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setCaptchaString(result);
    setCaptchaInput('');
  };

  useEffect(() => {
    generateCaptcha();
  }, [isRegistering]);

  const handleLogoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setLogoPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    // Validate ID format
    const idRegex = /^MS-\d{5}$/i;
    if (!idRegex.test(medId)) {
      setError('ID must be in the format MS-XXXXX (e.g., MS-12345)');
      return;
    }

    // Validate Captcha (case-insensitive for better UX)
    if (captchaInput.toLowerCase() !== captchaString.toLowerCase()) {
      setError('Incorrect Captcha. Please try again.');
      generateCaptcha();
      return;
    }

    setLoading(true);

    try {
      if (isRegistering) {
        if (!name.trim()) {
          throw new Error('Name is required for registration');
        }
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        
        // Initialize user document
        await setDoc(doc(db, 'users', userCredential.user.uid), {
          uid: userCredential.user.uid,
          medId: medId.toUpperCase(),
          name: name,
          email: email,
          role: 'Doctor'
        });
      } else {
        await signInWithEmailAndPassword(auth, email, password);
      }
      
      // Save logo to localStorage if uploaded
      if (logoPreview) {
        localStorage.setItem('logo', logoPreview);
      }
      
      onLogin();
    } catch (err: any) {
      setError(err.message || 'Failed to authenticate');
      generateCaptcha();
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setError(null);
    setLoading(true);
    try {
      const provider = new GoogleAuthProvider();
      const result = await signInWithPopup(auth, provider);
      
      // Check if user document exists, if not create it
      const userDocRef = doc(db, 'users', result.user.uid);
      const userDoc = await getDoc(userDocRef);
      
      if (!userDoc.exists()) {
        await setDoc(userDocRef, {
          uid: result.user.uid,
          medId: `MS-${Math.floor(10000 + Math.random() * 90000)}`, // Generate random ID for Google users
          name: result.user.displayName || 'Google User',
          email: result.user.email,
          role: 'Doctor'
        });
      }
      
      onLogin();
    } catch (err: any) {
      setError(err.message || 'Failed to authenticate with Google');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-950 p-4">
      <div className="bg-white dark:bg-gray-900 p-8 rounded-2xl border-2 border-gray-300 dark:border-dark-mode-green shadow-xl w-full max-w-md">
        
        {/* Circular Logo Upload at Top */}
        <div className="flex justify-center mb-6">
          <label className="relative w-24 h-24 rounded-full border-2 border-dashed border-gray-300 dark:border-dark-mode-green flex items-center justify-center cursor-pointer overflow-hidden group hover:border-teal-500 transition-colors bg-gray-50 dark:bg-gray-800">
            {logoPreview ? (
              <>
                <img src={logoPreview} alt="Logo" className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <Camera className="text-white" size={24} />
                </div>
              </>
            ) : (
              <div className="flex flex-col items-center text-gray-500">
                <Camera size={24} className="mb-1" />
                <span className="text-[10px] text-center px-2 leading-tight font-medium">Upload Logo</span>
              </div>
            )}
            <input type="file" accept="image/*" onChange={handleLogoUpload} className="hidden" />
          </label>
        </div>

        <h1 className="text-2xl font-bold text-center mb-6 text-black dark:text-dark-mode-green">
          {isRegistering ? 'MedScan AI Registration' : 'MedScan AI Login'}
        </h1>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegistering && (
            <div>
              <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 p-3 rounded-lg border border-gray-300 dark:border-dark-mode-green">
                <User size={20} className="text-gray-500" />
                <input type="text" placeholder="Full Name" value={name} onChange={(e) => setName(e.target.value)} className="bg-transparent w-full outline-none text-black dark:text-white" required={isRegistering} />
              </div>
            </div>
          )}

          <div>
            <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 p-3 rounded-lg border border-gray-300 dark:border-dark-mode-green">
              <Badge size={20} className="text-gray-500" />
              <input type="text" placeholder="ID (e.g., MS-12345)" value={medId} onChange={(e) => setMedId(e.target.value)} className="bg-transparent w-full outline-none text-black dark:text-white uppercase" required />
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 p-3 rounded-lg border border-gray-300 dark:border-dark-mode-green">
              <Mail size={20} className="text-gray-500" />
              <input type="email" placeholder="Email Address" value={email} onChange={(e) => setEmail(e.target.value)} className="bg-transparent w-full outline-none text-black dark:text-white" required />
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 p-3 rounded-lg border border-gray-300 dark:border-dark-mode-green">
              <Lock size={20} className="text-gray-500" />
              <input type={showPassword ? 'text' : 'password'} placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} className="bg-transparent w-full outline-none text-black dark:text-white" required />
              <button type="button" onClick={() => setShowPassword(!showPassword)} className="text-gray-500">
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          {/* Alphanumeric Captcha */}
          <div>
            <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 p-3 rounded-lg border border-gray-300 dark:border-dark-mode-green">
              <ShieldCheck size={20} className="text-gray-500 shrink-0" />
              <div className="bg-gray-200 dark:bg-gray-700 px-3 py-1 rounded font-mono font-bold text-lg tracking-widest text-black dark:text-white select-none relative overflow-hidden shrink-0">
                <span className="relative z-10">{captchaString}</span>
                <div className="absolute inset-0 opacity-30 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPgo8cmVjdCB3aWR0aD0iNCIgaGVpZ2h0PSI0IiBmaWxsPSIjZmZmIiAvPgo8cGF0aCBkPSJNMCAwTDRIDRaTTAgNEw0IDBaIiBzdHJva2U9IiMwMDAiIHN0cm9rZS13aWR0aD0iMSIgLz4KPC9zdmc+')]"></div>
              </div>
              <input type="text" placeholder="Enter Captcha" value={captchaInput} onChange={(e) => setCaptchaInput(e.target.value)} className="bg-transparent w-full outline-none text-black dark:text-white ml-2" required />
            </div>
          </div>

          {error && <p className="text-red-500 text-xs mt-1">{error}</p>}

          <button type="submit" disabled={loading} className="w-full bg-teal-600 dark:bg-dark-mode-green text-white p-3 rounded-lg font-bold hover:opacity-90 transition-opacity disabled:opacity-50">
            {loading ? 'Processing...' : (isRegistering ? 'Register' : 'Login')}
          </button>
          
          <div className="relative flex items-center py-2">
            <div className="flex-grow border-t border-gray-300 dark:border-gray-700"></div>
            <span className="flex-shrink-0 mx-4 text-gray-400 text-sm">Or continue with</span>
            <div className="flex-grow border-t border-gray-300 dark:border-gray-700"></div>
          </div>

          <button 
            type="button" 
            onClick={handleGoogleSignIn}
            disabled={loading} 
            className="w-full bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-600 p-3 rounded-lg font-bold hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
            </svg>
            Google
          </button>
          
          <button type="button" onClick={() => setIsRegistering(!isRegistering)} className="w-full text-sm text-teal-600 dark:text-teal-500 hover:underline mt-4">
            {isRegistering ? 'Already have an account? Login' : 'Need an account? Register'}
          </button>
        </form>
      </div>
    </div>
  );
}


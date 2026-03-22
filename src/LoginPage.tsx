import React, { useState, useEffect } from 'react';
import { User, IdCard, Lock, Upload, RefreshCw, Eye, EyeOff } from 'lucide-react';

export default function LoginPage({ onLogin, logo, setLogo }: { onLogin: () => void, logo: string | null, setLogo: (logo: string | null) => void }) {
  const [name, setName] = useState('');
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [captcha, setCaptcha] = useState({ answer: '' });
  const [userCaptcha, setUserCaptcha] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const getPasswordStrength = (pwd: string) => {
    if (!pwd) return '';
    if (pwd.length < 8) return 'Weak';
    if (/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,}$/.test(pwd)) return 'Strong';
    return 'Medium';
  };

  const strength = getPasswordStrength(password);
  const strengthColor = strength === 'Strong' ? 'text-green-500' : strength === 'Medium' ? 'text-yellow-500' : 'text-red-500';

  useEffect(() => {
    generateCaptcha();
  }, []);

  const generateCaptcha = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < 6; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setCaptcha({ answer: result });
    setUserCaptcha('');
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!name) newErrors.name = 'Full Name is required';
    if (!/^MS-\d{6}$/.test(userId)) newErrors.userId = 'User ID must be MS-XXXXXX';
    if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/.test(password)) {
      newErrors.password = 'Password must be 8+ chars, with uppercase, lowercase, number, and special char';
    }
    if (userCaptcha !== captcha.answer) newErrors.captcha = 'Incorrect CAPTCHA';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleLogoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setLogo(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-950 p-4">
      <div className="bg-white dark:bg-gray-900 p-8 rounded-2xl border-2 border-gray-300 dark:border-dark-mode-green shadow-xl w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-6 text-black dark:text-dark-mode-green">MedScan AI</h1>
        
        <div className="mb-6 flex flex-col items-center">
          {logo ? <img src={logo} alt="Logo" className="h-20 w-20 rounded-full object-cover mb-2" /> : <div className="h-20 w-20 rounded-full bg-gray-200 dark:bg-gray-800 flex items-center justify-center mb-2"><Upload className="text-gray-500" /></div>}
          <label className="cursor-pointer text-sm text-teal-600 dark:text-teal-500 hover:underline">
            Upload Logo
            <input type="file" className="hidden" onChange={handleLogoUpload} accept="image/*" />
          </label>
        </div>

        <div className="space-y-4">
          <div>
            <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 p-3 rounded-lg border border-gray-300 dark:border-dark-mode-green">
              <User size={20} className="text-gray-500" />
              <input type="text" placeholder="Full Name" value={name} onChange={(e) => setName(e.target.value)} className="bg-transparent w-full outline-none text-black dark:text-white" />
            </div>
            {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
          </div>

          <div>
            <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 p-3 rounded-lg border border-gray-300 dark:border-dark-mode-green">
              <IdCard size={20} className="text-gray-500" />
              <input type="text" placeholder="User ID (MS-XXXXXX)" value={userId} onChange={(e) => setUserId(e.target.value)} className="bg-transparent w-full outline-none text-black dark:text-white" />
            </div>
            {errors.userId && <p className="text-red-500 text-xs mt-1">{errors.userId}</p>}
          </div>

          <div>
            <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 p-3 rounded-lg border border-gray-300 dark:border-dark-mode-green">
              <Lock size={20} className="text-gray-500" />
              <input type={showPassword ? 'text' : 'password'} placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} className="bg-transparent w-full outline-none text-black dark:text-white" />
              <button onClick={() => setShowPassword(!showPassword)} className="text-gray-500">
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
            {password && <p className={`text-xs mt-1 font-bold ${strengthColor}`}>{strength}</p>}
            {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password}</p>}
          </div>

          <div className="flex items-center gap-4">
            <span className="text-black dark:text-dark-mode-green font-bold tracking-widest bg-gray-200 dark:bg-gray-800 p-2 rounded">{captcha.answer}</span>
            <input type="text" placeholder="Enter CAPTCHA" value={userCaptcha} onChange={(e) => setUserCaptcha(e.target.value)} className="bg-gray-100 dark:bg-gray-800 p-3 rounded-lg border border-gray-300 dark:border-dark-mode-green w-32 text-center text-black dark:text-white" />
            <button onClick={generateCaptcha}><RefreshCw size={20} className="text-gray-500" /></button>
          </div>
          {errors.captcha && <p className="text-red-500 text-xs mt-1">{errors.captcha}</p>}

          <button onClick={() => validate() && onLogin()} className="w-full bg-teal-600 dark:bg-dark-mode-green text-white p-3 rounded-lg font-bold hover:opacity-90 transition-opacity">
            Login
          </button>
        </div>
      </div>
    </div>
  );
}

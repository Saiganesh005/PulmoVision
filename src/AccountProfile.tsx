import React, { useState } from 'react';
import { User, Shield, Building, Camera, Save, X, Edit2 } from 'lucide-react';

export default function AccountProfile() {
  const [isEditing, setIsEditing] = useState(false);
  const [profile, setProfile] = useState({
    name: 'Dr. John Doe',
    role: 'Radiologist',
    email: 'john.doe@hospital.com',
    phone: '+1 234 567 890',
    org: 'City General Hospital',
    dept: 'Radiology',
    location: 'New York, USA',
  });

  const handleSave = () => {
    // In a real app, send to backend
    setIsEditing(false);
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  return (
    <div className="p-8 max-w-4xl mx-auto text-black dark:text-dark-mode-green font-serif">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Account Profile</h1>
        {!isEditing ? (
          <button onClick={() => setIsEditing(true)} className="flex items-center gap-2 bg-gray-200 dark:bg-dark-mode-green text-black dark:text-white px-4 py-2 rounded-lg">
            <Edit2 size={18} /> Edit Profile
          </button>
        ) : (
          <div className="flex gap-2">
            <button onClick={handleCancel} className="flex items-center gap-2 bg-gray-300 dark:bg-gray-700 text-black dark:text-white px-4 py-2 rounded-lg">
              <X size={18} /> Cancel
            </button>
            <button onClick={handleSave} className="flex items-center gap-2 bg-gray-200 dark:bg-dark-mode-green text-black dark:text-white px-4 py-2 rounded-lg">
              <Save size={18} /> Save Changes
            </button>
          </div>
        )}
      </div>

      {/* Profile Information */}
      <section className="bg-gray-100 dark:bg-gray-900 p-6 rounded-xl border-2 border-gray-300 dark:border-dark-mode-green mb-6">
        <div className="flex items-center gap-3 mb-6">
          <User className="text-black dark:text-dark-mode-green" />
          <h2 className="text-xl font-bold">Profile Information</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex flex-col items-center gap-4">
            <div className="w-24 h-24 bg-gray-200 dark:bg-gray-800 rounded-full flex items-center justify-center border-2 border-gray-300 dark:border-dark-mode-green">
              <Camera className="text-black dark:text-dark-mode-green" />
            </div>
            {isEditing && <button className="text-sm text-teal-600 dark:text-teal-500">Change Avatar</button>}
          </div>
          <div className="space-y-4">
            <input type="text" value={profile.name} disabled={!isEditing} onChange={(e) => setProfile({...profile, name: e.target.value})} className="w-full p-3 bg-gray-200 dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-dark-mode-green" />
            <select value={profile.role} disabled={!isEditing} onChange={(e) => setProfile({...profile, role: e.target.value})} className="w-full p-3 bg-gray-200 dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-dark-mode-green">
              <option>Doctor</option>
              <option>Radiologist</option>
              <option>Admin</option>
              <option>Researcher</option>
              <option>Student</option>
            </select>
            <input type="email" value={profile.email} disabled={!isEditing} onChange={(e) => setProfile({...profile, email: e.target.value})} className="w-full p-3 bg-gray-200 dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-dark-mode-green" />
            <input type="tel" value={profile.phone} disabled={!isEditing} onChange={(e) => setProfile({...profile, phone: e.target.value})} className="w-full p-3 bg-gray-200 dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-dark-mode-green" />
          </div>
        </div>
      </section>

      {/* Account Details */}
      <section className="bg-gray-100 dark:bg-gray-900 p-6 rounded-xl border-2 border-gray-300 dark:border-dark-mode-green mb-6">
        <div className="flex items-center gap-3 mb-6">
          <Building className="text-black dark:text-dark-mode-green" />
          <h2 className="text-xl font-bold">Account Details</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input type="text" value="UID: 12345-ABCDE" disabled className="w-full p-3 bg-gray-200 dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-dark-mode-green opacity-70" />
          <input type="text" value={profile.org} disabled={!isEditing} onChange={(e) => setProfile({...profile, org: e.target.value})} className="w-full p-3 bg-gray-200 dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-dark-mode-green" />
          <input type="text" value={profile.dept} disabled={!isEditing} onChange={(e) => setProfile({...profile, dept: e.target.value})} className="w-full p-3 bg-gray-200 dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-dark-mode-green" />
          <input type="text" value={profile.location} disabled={!isEditing} onChange={(e) => setProfile({...profile, location: e.target.value})} className="w-full p-3 bg-gray-200 dark:bg-gray-800 rounded-lg border border-gray-300 dark:border-dark-mode-green" />
        </div>
      </section>

      {/* Security Settings */}
      <section className="bg-gray-100 dark:bg-gray-900 p-6 rounded-xl border-2 border-gray-300 dark:border-dark-mode-green">
        <div className="flex items-center gap-3 mb-6">
          <Shield className="text-black dark:text-dark-mode-green" />
          <h2 className="text-xl font-bold">Security Settings</h2>
        </div>
        <div className="space-y-4">
          <button className="text-teal-600 dark:text-teal-500">Change Password</button>
          <div className="flex items-center justify-between">
            <span>Enable Two-Factor Authentication (2FA)</span>
            <input type="checkbox" className="w-6 h-6 accent-teal-600 dark:accent-dark-mode-green" />
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-500">Last login: March 17, 2026, 07:00 AM from Chrome on Windows</p>
        </div>
      </section>
    </div>
  );
}

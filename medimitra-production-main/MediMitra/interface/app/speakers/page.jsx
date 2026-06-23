"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import NavbarInternal from "../components/NavbarInternal";

export default function SpeakerSetup() {
  const { data: session } = useSession();
  const [users, setUsers] = useState([]);
  const [speakers, setSpeakers] = useState([]);
  const [selectedUser, setSelectedUser] = useState("");
  const [selectedSpeaker, setSelectedSpeaker] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const piUrl = "https://overreach-presuming-surprise.ngrok-free.dev";

  useEffect(() => {
    fetchSpeakers();
    if (session?.user?.email) {
      fetchUsers();
    }
  }, [session]);

  const fetchSpeakers = async () => {
    try {
      const res = await fetch(`${piUrl}/speakers/scan`, {
        headers: {
          "ngrok-skip-browser-warning": "true"
        }
      });
      const data = await res.json();
      setSpeakers(data.speakers || []);
    } catch (err) {
      console.error("Error fetching speakers", err);
      setSpeakers([]);
    }
  };

  const fetchUsers = async () => {
    try {
      // Fetch from the Next.js API so we get the correctly saved members
      const res = await fetch("/api/member");
      const data = await res.json();
      if (Array.isArray(data)) {
        setUsers(data);
      } else {
        setUsers([]);
      }
    } catch (err) {
      console.error("Error fetching users", err);
    }
  };

  const testSpeaker = async () => {
    if (!selectedSpeaker) {
      setMessage("⚠️ Select a speaker first");
      return;
    }

    if (!selectedUser) {
      setMessage("⚠️ Select a family member first");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const params = new URLSearchParams({
        family_member: selectedUser.trim(),
        speaker_id: selectedSpeaker.speaker_id
      });

      const res = await fetch(
        `${piUrl}/speakers/test?${params.toString()}`,
        { 
          method: "POST",
          headers: {
            "ngrok-skip-browser-warning": "true"
          }
        }
      );

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Request failed");
      }

      setMessage("🔊 Test sound played");
    } catch (err) {
      setMessage(`❌ ${err.message || "Failed to play test sound"}`);
    }

    setLoading(false);
  };


  const saveMapping = async () => {
    if (!selectedSpeaker || !selectedUser) {
      setMessage("⚠️ Select both user and speaker");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      await fetch(`${piUrl}/speakers/map`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "ngrok-skip-browser-warning": "true"
        },
        body: JSON.stringify({
          family_member: selectedUser,
          speaker_id: selectedSpeaker.speaker_id,
          mac: selectedSpeaker.mac,
          sink: selectedSpeaker.sink
        })
      });

      setMessage("✅ Speaker mapped successfully");
    } catch (err) {
      setMessage("❌ Failed to save mapping");
    }

    setLoading(false);
  };

  return (
    <div className="w-screen h-screen flex flex-col bg-gradient-to-r from-[#0F081A] to-black">
      <NavbarInternal />
      <div className="flex flex-col items-center justify-center flex-grow p-6 text-white pt-24">
        <div className="w-full max-w-md bg-white/10 p-8 rounded-xl shadow-lg backdrop-blur-md border border-gray-800">
          <h1 className="text-3xl font-bold mb-6 text-center text-white">
            🔊 Speaker Setup
          </h1>

          {/* User Selector */}
          <div className="mt-4">
            <label className="text-gray-300 font-semibold mb-2 block">Family Member</label>
            <select
              value={selectedUser}
              onChange={e => setSelectedUser(e.target.value)}
              className="w-full p-3 bg-gray-900 text-white rounded-lg border border-gray-600 focus:outline-none focus:border-purple-500 transition-colors"
            >
              <option value="" className="bg-gray-900 text-gray-400">Select family member</option>
              {users.map(user => (
                <option key={user._id || user.name} value={user.name} className="bg-gray-900 text-white">
                  {user.name}
                </option>
              ))}
            </select>
            {users.length === 0 && (
               <p className="text-yellow-400 text-xs mt-2">No members found. Please add a member in the Dashboard first.</p>
            )}
          </div>

          {/* Speaker List */}
          <div className="mt-6">
            <label className="text-gray-300 font-semibold mb-2 block">Available Speakers</label>
            <div className="mt-2 bg-gray-900 rounded-lg p-4 border border-gray-600 max-h-48 overflow-y-auto">
              {speakers.length === 0 ? (
                <p className="text-gray-400 text-sm">No Bluetooth speakers detected</p>
              ) : (
                speakers.map(sp => (
                  <label
                    key={sp.mac}
                    className="flex items-center mb-3 cursor-pointer group"
                  >
                    <input
                      type="radio"
                      name="speaker"
                      className="w-4 h-4 text-purple-600 bg-gray-800 border-gray-600 focus:ring-purple-500"
                      onChange={() => setSelectedSpeaker(sp)}
                    />
                    <span className="ml-3 text-gray-300 group-hover:text-white transition-colors">
                      {sp.mac}
                    </span>
                  </label>
                ))
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="mt-8 flex flex-col sm:flex-row gap-4">
            <button
              onClick={testSpeaker}
              disabled={loading}
              className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-3 px-4 rounded-lg transition duration-300 disabled:opacity-50"
            >
              🔊 Test
            </button>

            <button
              onClick={saveMapping}
              disabled={loading}
              className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-4 rounded-lg shadow-lg transition duration-300 disabled:opacity-50"
            >
              💾 Save
            </button>
          </div>

          {/* Status Message */}
          {message && (
            <div className={`mt-6 p-4 rounded-lg text-center font-medium ${message.includes('✅') || message.includes('🔊') ? 'bg-green-900/50 text-green-200 border border-green-800' : 'bg-red-900/50 text-red-200 border border-red-800'}`}>
              {message}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

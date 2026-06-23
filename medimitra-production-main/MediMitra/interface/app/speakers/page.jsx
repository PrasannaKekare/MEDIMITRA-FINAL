"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";

export default function SpeakerSetup() {
  const { data: session } = useSession();
  const [users, setUsers] = useState({});
  const [speakers, setSpeakers] = useState([]);
  const [selectedUser, setSelectedUser] = useState("");
  const [selectedSpeaker, setSelectedSpeaker] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const [piUrl, setPiUrl] = useState("https://medimitra-final.onrender.com")

  useEffect(() => {
    if (typeof window !== "undefined") {
      setPiUrl("https://medimitra-final.onrender.com");
    }
  }, []);

  useEffect(() => {
    fetchSpeakers();
    if (session?.user?.email) {
      fetchUsers(session.user.email);
    }
  }, [session, piUrl]);

  const fetchSpeakers = async () => {
    try {
      const res = await fetch(`${piUrl}/speakers/scan`);
      const data = await res.json();
      setSpeakers(data.speakers || []);
    } catch (err) {
      console.error("Error fetching speakers", err);
      setSpeakers([]);
    }
  };

  const fetchUsers = async (email) => {
    try {
      const res = await fetch(`${piUrl}/users/${email}/family`);
      const data = await res.json();
      setUsers(data);
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
        { method: "POST" }
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
        headers: { "Content-Type": "application/json" },
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
    <div style={{ padding: 24, maxWidth: 600 }}>
      <h1 style={{ fontSize: 22, fontWeight: "bold" }}>
        🔊 Speaker Setup
      </h1>

      {/* User Selector */}
      <div style={{ marginTop: 16 }}>
        <label>Family Member</label>
        <select
          value={selectedUser}
          onChange={e => setSelectedUser(e.target.value)}
          style={{ width: "100%", padding: 8, marginTop: 6 }}
        >
          <option value="">Select family member</option>
          {Object.keys(users).map(name => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </div>

      {/* Speaker List */}
      <div style={{ marginTop: 24 }}>
        <label>Available Speakers</label>
        <div style={{ marginTop: 10 }}>
          {speakers.length === 0 && (
            <p>No Bluetooth speakers detected</p>
          )}

          {speakers.map(sp => (
            <label
              key={sp.mac}
              style={{ display: "block", marginBottom: 8 }}
            >
              <input
                type="radio"
                name="speaker"
                onChange={() => setSelectedSpeaker(sp)}
              />
              <span style={{ marginLeft: 8 }}>
                {sp.mac}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div style={{ marginTop: 24 }}>
        <button
          onClick={testSpeaker}
          disabled={loading}
          style={{ marginRight: 12 }}
        >
          🔊 Test Speaker
        </button>

        <button
          onClick={saveMapping}
          disabled={loading}
        >
          💾 Save Mapping
        </button>
      </div>

      {/* Status Message */}
      {message && (
        <p style={{ marginTop: 16 }}>
          {message}
        </p>
      )}
    </div>
  );
}

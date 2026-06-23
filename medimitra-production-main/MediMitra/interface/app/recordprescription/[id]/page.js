"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useSession } from "next-auth/react";
import { FaMicrophone, FaKeyboard } from "react-icons/fa";

export default function SpeechToText() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [recognition, setRecognition] = useState(null);
  const [inputMode, setInputMode] = useState("voice"); // voice | text

  const { id } = useParams();
  const { data: session } = useSession();
  const [email, setEmail] = useState("");
  const [familyMemberId, setFamilyMemberId] = useState("");

  useEffect(() => {
    if (session) setEmail(session.user.email);
    if (id) setFamilyMemberId(id);
  }, [session, id]);

  // 🎤 Speech Recognition Setup
  useEffect(() => {
    if (
      typeof window !== "undefined" &&
      "webkitSpeechRecognition" in window
    ) {
      const recognitionInstance = new webkitSpeechRecognition();
      recognitionInstance.continuous = true;
      recognitionInstance.interimResults = true;
      recognitionInstance.lang = "en-US";

      recognitionInstance.onresult = (event) => {
        let finalTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          finalTranscript += event.results[i][0].transcript;
        }
        setTranscript(finalTranscript);
      };

      recognitionInstance.onerror = () => {
        // auto-fallback if mic fails
        setInputMode("text");
        setIsRecording(false);
      };

      setRecognition(recognitionInstance);
    } else {
      setInputMode("text");
    }
  }, []);

  const startRecording = () => {
    if (recognition && !isRecording) {
      recognition.start();
      setIsRecording(true);
    }
  };

  const stopRecording = () => {
    if (recognition && isRecording) {
      recognition.stop();
      setIsRecording(false);
    }
  };

  const handleSubmit = async () => {
    if (!transcript.trim()) {
      alert("Please enter or record some text");
      return;
    }

    const formData = new FormData();
    formData.append("user_name", email);
    formData.append("family_member_id", familyMemberId);
    formData.append("transcript", transcript);

    try {
      const piUrl = "https://overreach-presuming-surprise.ngrok-free.dev";

      const response = await fetch(`${piUrl}/audio-prescription/`, {
        method: "POST",
        headers: {
          "ngrok-skip-browser-warning": "true"
        },
        body: formData,
      });

      const data = await response.json();
      console.log("Response from FastAPI:", data);
      alert("Voice prescription processed successfully!");
    } catch (error) {
      console.error("Error submitting transcript:", error);
      alert("Failed to process voice prescription.");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h1 className="text-5xl font-dm mb-6">
        Record or Type your Prescription
      </h1>

      {/* MODE TOGGLE */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => setInputMode("voice")}
          className={`px-4 py-2 rounded-lg ${
            inputMode === "voice"
              ? "bg-purple-500 text-white"
              : "bg-gray-200 text-black"
          }`}
        >
          <FaMicrophone className="inline mr-2" />
          Voice
        </button>

        <button
          onClick={() => {
            if (isRecording) stopRecording();
            setInputMode("text");
          }}
          className={`px-4 py-2 rounded-lg ${
            inputMode === "text"
              ? "bg-purple-500 text-white"
              : "bg-gray-200 text-black"
          }`}
        >
          <FaKeyboard className="inline mr-2" />
          Text
        </button>
      </div>

      {/* VOICE MODE */}
      {inputMode === "voice" && (
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={`px-6 py-3 text-black text-2xl font-semibold rounded-xl border-4 border-gray-400 flex items-center ${
            isRecording ? "bg-red-500" : "bg-white"
          } hover:bg-purple-500 hover:text-white`}
        >
          <FaMicrophone className="mr-2" />
          {isRecording ? "Stop Recording" : "Start Recording"}
        </button>
      )}

      {/* TEXTAREA (shared) */}
      <textarea
        className="mt-10 p-4 w-3/4 h-48 border border-purple-500 rounded-md text-black bg-transparent"
        value={transcript}
        onChange={(e) => setTranscript(e.target.value)}
        readOnly={inputMode === "voice"}
        placeholder={
          inputMode === "voice"
            ? "Speech will appear here..."
            : "Type your prescription here..."
        }
      />

      <button
        onClick={handleSubmit}
        className="px-6 py-3 mt-6 text-black text-2xl font-dm border-4 border-gray-400 font-semibold rounded-xl bg-white hover:bg-purple-500 hover:text-white"
      >
        Submit
      </button>
    </div>
  );
}

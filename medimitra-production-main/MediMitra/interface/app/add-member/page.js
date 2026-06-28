"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import NavbarInternal from "../components/NavbarInternal";
import Spinner from "../components/Spinner";
import ButtonSpinner from "../components/ButtonSpinner";

export default function AddMember() {
  const { data: session, status } = useSession(); // Access session to get the email
  const router = useRouter();
  const [name, setName] = useState("");
  const [dob, setDob] = useState("");
  const [breakfastTime, setBreakfastTime] = useState("");
  const [lunchTime, setLunchTime] = useState("");
  const [dinnerTime, setDinnerTime] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!session?.user?.email) {
      alert("User is not logged in");
      return;
    }
    
    setIsLoading(true);

    // Format the meal times
    const formattedBreakfast = `${breakfastTime}`;
    const formattedLunch = `${lunchTime}`;
    const formattedDinner = `${dinnerTime}`;

    // Get the logged-in user's email
    const userEmail = session.user.email;

    console.log("Submitting member for user:", userEmail);

    try {
      // Send data to the FastAPI backend
      // We use a try-catch here so that if FastAPI is unreachable, we can still log it
      const piUrl = "https://medimitra-final.onrender.com";
      const fastAPIresponse = await fetch(`${piUrl}/users/` + userEmail + '/family/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          family_name: name,
          dob,
          breakfast: formattedBreakfast,
          lunch: formattedLunch,
          dinner: formattedDinner,
        }),
      });
      
      if (!fastAPIresponse.ok) {
        console.warn("FastAPI member creation returned non-OK status:", fastAPIresponse.status);
      }
    } catch (err) {
      console.error(`Failed to connect to FastAPI at the Pi's IP. Ensure the backend is running.`, err);
      // We don't return here because we still want to try saving to the main database
    }

    try {
      const response = await fetch("/api/member", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            name,
            dob,
            Breakfast: formattedBreakfast,
            Lunch: formattedLunch,
            Dinner: formattedDinner,
        }),
      });

      if (response.ok) {
        const newMember = await response.json();
        console.log("Member created successfully in main DB:", newMember);
        alert("New family member added successfully!");
        router.push(`/new-member`);
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error("Failed to add member to main DB:", response.status, errorData);
        alert(`Failed to add member: ${errorData.message || "Server Error"}`);
      }
    } catch (err) {
      console.error("Network error calling /api/member:", err);
      alert("Network error. Please check your connection.");
    } finally {
      setIsLoading(false);
    }
  };

  if (status === "unauthenticated") {
    router.push("/login");
  }

  if (status === "loading") {
    return <Spinner />;
  }

  if (status === "authenticated") {
    return (
      <>
      <div className="w-screen h-full relative bg-[url('/blur-purple.svg')] bg-cover ">
  <NavbarInternal />

  {/* Main Section */}
  <div id="main" className="w-full h-full bg-gradient-to-r from-[#0F081A] to-black">
    <div className="flex justify-center items-center w-full h-full pt-24">
      <div className="w-[90%] md:w-[70%] lg:w-[40%] bg-[#000000] border border-purple-800 p-8 rounded-lg shadow-xl">
        <h1 className="text-4xl font-dm font-bold text-center text-white mb-5">
          Add New Family Member
        </h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Name
            </label>
            <input
              type="text"
              className="block w-full p-3 bg-black text-white border border-purple-900 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 shadow-md"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Date of Birth
            </label>
            <input
              type="date"
              className="block w-full p-3 bg-black text-white border border-purple-900 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 shadow-md"
              value={dob}
              onChange={(e) => setDob(e.target.value)}
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Breakfast Time
              </label>
              <input
                type="time"
                className="block w-full p-3 bg-black text-white border border-purple-800 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 shadow-md"
                value={breakfastTime}
                onChange={(e) => setBreakfastTime(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Lunch Time
              </label>
              <input
                type="time"
                className="block w-full p-3 bg-black text-white border border-purple-800 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 shadow-md"
                value={lunchTime}
                onChange={(e) => setLunchTime(e.target.value)}
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Dinner Time
            </label>
            <input
              type="time"
              className="block w-full p-3 bg-black text-white border border-purple-800 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500 shadow-md"
              value={dinnerTime}
              onChange={(e) => setDinnerTime(e.target.value)}
              required
            />
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full p-3 bg-white text-black rounded-lg shadow-lg font-dm hover:bg-purple-500 hover:text-white transition-transform transform hover:scale-105 disabled:bg-gray-500 disabled:cursor-not-allowed disabled:transform-none flex justify-center items-center gap-2"
            >
              {isLoading && <ButtonSpinner className="text-current" />}
              {isLoading ? "Submitting..." : "Submit"}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>

      </>
    );
  }
}

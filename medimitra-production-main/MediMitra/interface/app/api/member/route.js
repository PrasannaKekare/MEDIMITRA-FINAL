import connect from "../../../utils/db";
import Member from "../../../models/member";
import User from "../../../models/User";
import { getServerSession } from "next-auth/next";
import { NextResponse } from "next/server";
import { authOptions } from "../auth/[...nextauth]/route";

export async function POST(req) {
  console.log("POST request received at /api/member");

  try {
    const session = await getServerSession(authOptions);
    console.log("Session retrieved:", session ? "YES" : "NO");

    await connect();

    if (!session || !session.user?.email) {
      console.error("Unauthorized access attempt: No session or email");
      return new NextResponse("Unauthorized", { status: 401 });
    }

    // Parse the request body
    const body = await req.json();
    const { name, dob, Breakfast, Lunch, Dinner } = body;

    console.log("Received Data for user:", session.user.email, { name, dob, Breakfast, Lunch, Dinner });

    const { email: userEmail } = session.user;

    const user = await User.findOne({ email: userEmail });
    if (!user) {
        console.error(`User with email ${userEmail} not found in database`);
        return new NextResponse(`User with email ${userEmail} not found` , {
            status: 404,
        });
    }

    console.log("User found in DB:", user._id);

    const newMember = new Member({ name, dob, Breakfast, Lunch, Dinner, user: user._id });
    
    // Ensure the user has a members array
    if (!user.members) {
        console.log("Initializing members array for user");
        user.members = [];
    }

    user.members.push(newMember._id);
    
    console.log("Saving user...");
    await user.save(); 

    console.log("Saving new member...");
    await newMember.save();

    console.log("New member added successfully:", newMember._id);
    return new Response(JSON.stringify(newMember), {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('CRITICAL ERROR in /api/member POST:', error);
    return new Response(JSON.stringify({ 
        message: 'Error adding member.', 
        error: error.message 
    }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
    });
  }
}

// Add the GET method
export async function GET(req) {
  console.log("GET request received at /api/member");

  const session = await getServerSession(authOptions);
  await connect();

  if (!session || !session.user?.email) {
    console.error("Unauthorized access attempt");
    return new NextResponse("Unauthorized", { status: 401 });
  }

  try {
    const { email: userEmail } = session.user;

    const user = await User.findOne({ email: userEmail });
    if (!user) {
      console.error(`User with email ${userEmail} not found`);
      return new NextResponse(`User with email ${userEmail} not found`, {
        status: 404,
      });
    }

    // Find all members associated with the user
    const members = await Member.find({ user: user._id });
    console.log("Fetched members:", members);

    return new Response(JSON.stringify(members), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("Error fetching members:", error);
    return new Response(
      JSON.stringify({
        message: "Error fetching members.",
        error: error.message,
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
}

import mongoose from "mongoose";

// Connection function
const connect = async () => {
  // Check if there's an existing connection and if it's ready
  if (mongoose.connections[0].readyState) {
    console.log("Already connected to  sushantMongoDB.");
    return; // If connected, return early
  }
  // console.log(process.env.MONGO_URL);
  try {
    // Connect to MongoDB with connection options
    await mongoose.connect(
      "mongodb+srv://prasanna:nGiZt8iWMh7nRiCR@proj.fqffb3j.mongodb.net/"
      // useNewUrlParser: true,
      // useUnifiedTopology: true,
    );
    console.log("Connection to MongoDB sushant established");
  } catch (error) {
    console.error("Error connecting to MongoDB:", error.message);
    throw new Error("Failed to connect to MongoDB.");
  }
};

export default connect;

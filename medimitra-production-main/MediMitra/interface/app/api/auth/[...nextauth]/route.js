import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import CredentialsProvider from "next-auth/providers/credentials";
import bcrypt from "bcryptjs";
import User from "../../../../models/User";
import connect from "../../../../utils/db";

 const authOptions = {
  secret: process.env.NEXTAUTH_SECRET,
  session: { strategy: "jwt" },
  providers: [
    CredentialsProvider({
      id: "credentials",
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        await connect();

        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        const user = await User.findOne({ email: credentials.email });

        if (!user || !user.password) {
          return null;
        }

        const isPasswordCorrect = await bcrypt.compare(
          credentials.password, // plain password
          user.password         // hashed password
        );

        console.log("PASSWORD MATCH:", isPasswordCorrect);

        if (!isPasswordCorrect) {
          return null;
        }

        // ✅ return plain object
        return {
          id: user._id.toString(),
          email: user.email,
        };
      },
    }),

    // ✅ COMMA WAS MISSING HERE
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    }),
  ],

  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "credentials") {
        return true;
      }

      if (account?.provider === "google") {
        await connect();
        try {
          const existingUser = await User.findOne({ email: user.email });
          if (!existingUser) {
            await new User({ email: user.email }).save();
          }
          return true;
        } catch (err) {
          console.log("Error saving user", err);
          return false;
        }
      }

      return false;
    },
  },
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { SwrProvider } from "@/components/swr-provider";
import { NavBar } from "@/components/nav-bar";

const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "TicketBooking.pk | Premium Ticket Booking Platform",
  description: "Experience the easiest way to book bus, train, and flight tickets across Pakistan. Instant lock, secure payments, and premium customer service.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} relative min-h-screen text-slate-100 bg-[#070913] antialiased`}>
        {/* Glow Blobs Background */}
        <div className="pointer-events-none fixed inset-0 -z-20 overflow-hidden opacity-45">
          <div className="absolute top-[-10%] left-[-10%] h-[500px] w-[500px] rounded-full bg-blue-600/20 blur-[120px] animate-float" />
          <div className="absolute bottom-[10%] right-[-10%] h-[600px] w-[600px] rounded-full bg-indigo-600/15 blur-[150px] animate-float-reverse" />
          <div className="absolute top-[40%] right-[20%] h-[350px] w-[350px] rounded-full bg-purple-600/10 blur-[100px] animate-float" />
          <div className="absolute bottom-[30%] left-[10%] h-[400px] w-[400px] rounded-full bg-emerald-600/10 blur-[130px] animate-float-reverse" />
        </div>
        <SwrProvider>
          <NavBar />
          <main className="mx-auto max-w-5xl px-4 py-8 relative z-10">{children}</main>
        </SwrProvider>
      </body>
    </html>
  );
}

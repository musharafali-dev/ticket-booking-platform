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
        {/* Glow Blobs and Grid Background */}
        <div className="pointer-events-none fixed inset-0 -z-20 overflow-hidden bg-[#070913]">
          {/* Grid pattern */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:3rem_3rem]" />
          
          {/* Orange/Amber and Blue glowing radial blobs */}
          <div className="absolute top-[-10%] left-[-10%] h-[550px] w-[550px] rounded-full bg-blue-600/15 blur-[120px] animate-float" />
          <div className="absolute bottom-[10%] right-[-10%] h-[650px] w-[650px] rounded-full bg-orange-600/10 blur-[150px] animate-float-reverse" />
          <div className="absolute top-[35%] right-[15%] h-[400px] w-[400px] rounded-full bg-amber-500/10 blur-[110px] animate-float" />
          <div className="absolute bottom-[25%] left-[5%] h-[450px] w-[450px] rounded-full bg-blue-500/10 blur-[130px] animate-float-reverse" />
        </div>
        <SwrProvider>
          <NavBar />
          <main className="mx-auto max-w-5xl px-4 py-8 relative z-10">{children}</main>
        </SwrProvider>
      </body>
    </html>
  );
}

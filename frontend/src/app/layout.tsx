import type { Metadata } from "next";
import "./globals.css";
import { SwrProvider } from "@/components/swr-provider";
import { NavBar } from "@/components/nav-bar";

export const metadata: Metadata = {
  title: "Ticket Booking Platform | Pakistan",
  description: "Book bus, train, and airplane tickets across Pakistan",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <SwrProvider>
          <NavBar />
          <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
        </SwrProvider>
      </body>
    </html>
  );
}

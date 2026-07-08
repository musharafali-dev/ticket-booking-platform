"use client";

import { useState } from "react";
import { Button } from "@/components/button";
import Link from "next/link";

type TabType = "all" | "transport" | "tech" | "payments";

export default function ServicesPage() {
  const [activeTab, setActiveTab] = useState<TabType>("all");

  const categories = [
    { id: "all", label: "All Services" },
    { id: "transport", label: "Transport Modes" },
    { id: "tech", label: "Security & Tech" },
    { id: "payments", label: "Payment Options" },
  ];

  const features = [
    // Transport Services
    {
      id: "bus",
      category: "transport",
      title: "Premium Bus Ticketing",
      description: "Book executive and luxury bus services across Pakistan's major highways (M-2, M-3, M-9). Real-time seat layouts, terminal locations, and boarding details.",
      icon: (
        <svg className="w-6 h-6 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      ),
      tags: ["Daewoo", "Faisal Movers", "Sania Express"],
      highlight: "Luxury & Executive coaches",
      link: "/?type=BUS",
      btnText: "Book Bus Tickets",
    },
    {
      id: "train",
      category: "transport",
      title: "Railways Reservations",
      description: "Instant booking for Pakistan Railways' major lines. Select AC Sleeper, AC Business, AC Standard, or Economy berths. Live schedule tracker and seat mapping.",
      icon: (
        <svg className="w-6 h-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      tags: ["Green Line", "Tezgam", "Karakoram"],
      highlight: "AC Sleeper & Standard berths",
      link: "/?type=TRAIN",
      btnText: "Book Train Tickets",
    },
    {
      id: "flight",
      category: "transport",
      title: "Domestic Flights",
      description: "Compare and book domestic air travel. Instant flight schedules, baggage allowances, check-in details, and boarding pass instructions.",
      icon: (
        <svg className="w-6 h-6 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      ),
      tags: ["PIA", "AirSial", "Serene Air", "Fly Jinnah"],
      highlight: "All major domestic airlines",
      link: "/?type=AIRPLANE",
      btnText: "Book Flight Tickets",
    },
    // Tech & Security
    {
      id: "lock",
      category: "tech",
      title: "Temporary Seat Locking",
      description: "Our advanced concurrency system locks your selected seats for 10 minutes during the checkout process. Zero double-bookings, 100% reservation guarantee.",
      icon: (
        <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      ),
      tags: ["Concurrency-safe", "PostgreSQL advisory locks", "10-min grace period"],
      highlight: "Guaranteed Seat Availability",
      link: "/",
      btnText: "Start Booking",
    },
    {
      id: "cancellation",
      category: "tech",
      title: "Easy Cancellation & Refunds",
      description: "Need to change plans? Cancel bookings directly from your dashboard with one click. Seats are automatically released back to the general inventory instantly.",
      icon: (
        <svg className="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      tags: ["Self-service", "Instant seat release", "Flexible policies"],
      highlight: "No-fuss ticket cancellation",
      link: "/bookings",
      btnText: "Manage Bookings",
    },
    // Payments
    {
      id: "local-pay",
      category: "payments",
      title: "Localized Mobile Wallets",
      description: "Direct integrations with Pakistan's leading mobile wallets. Secure authentication, instant checkouts, and digital receipt generation.",
      icon: (
        <svg className="w-6 h-6 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      tags: ["EasyPaisa", "JazzCash", "Mock Gateway Enabled"],
      highlight: "No credit card required",
      link: "/",
      btnText: "Proceed to Booking",
    },
    {
      id: "cards",
      category: "payments",
      title: "Debit & Credit Cards",
      description: "Supports all major global and local card processors. Encrypted merchant flow complying with local security standards.",
      icon: (
        <svg className="w-6 h-6 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
        </svg>
      ),
      tags: ["Visa", "Mastercard", "UnionPay", "PayPak"],
      highlight: "Fast checkout using 3D secure",
      link: "/",
      btnText: "Proceed to Booking",
    },
  ];

  const filteredFeatures = activeTab === "all" 
    ? features 
    : features.filter(f => f.category === activeTab);

  return (
    <div className="flex flex-col gap-10 max-w-4xl mx-auto py-4">
      {/* Header section */}
      <div className="text-center">
        <h1 className="mb-4 text-4xl font-extrabold tracking-tight sm:text-5xl bg-gradient-to-r from-orange-400 via-amber-200 to-indigo-400 bg-clip-text text-transparent">
          Our Services & Features
        </h1>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto font-medium">
          TicketBooking.pk provides a secure, lightning-fast platform to search, reserve, and pay for your travel tickets all in one place.
        </p>
      </div>

      {/* Interactive Tabs */}
      <div className="flex flex-wrap items-center justify-center gap-2 border-b border-white/5 pb-6">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setActiveTab(cat.id as TabType)}
            className={`px-4 py-2 text-sm font-semibold rounded-lg transition duration-200 ${
              activeTab === cat.id
                ? "bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-[0_4px_12px_rgba(249,115,22,0.15)]"
                : "bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white border border-white/5"
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredFeatures.map((feat) => (
          <div
            key={feat.id}
            className="group relative flex flex-col justify-between rounded-2xl glass-panel p-6 border-white/5 shadow-xl hover:border-white/10 hover:shadow-2xl transition-all duration-300 overflow-hidden"
          >
            {/* Top accent line */}
            <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r ${
              feat.category === "transport" ? "from-blue-500 to-indigo-500" :
              feat.category === "tech" ? "from-emerald-500 to-teal-500" :
              "from-orange-500 to-amber-500"
            }`} />

            <div>
              {/* Icon & Title */}
              <div className="flex items-center gap-4 mb-4">
                <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-white/5 border border-white/5 group-hover:bg-white/10 group-hover:scale-105 transition-all duration-300">
                  {feat.icon}
                </div>
                <h3 className="text-xl font-bold text-white tracking-tight">{feat.title}</h3>
              </div>

              {/* Description */}
              <p className="text-slate-300 text-sm leading-relaxed mb-6 font-medium">
                {feat.description}
              </p>
            </div>

            {/* Bottom details */}
            <div className="mt-auto flex flex-col gap-4">
              <div>
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {feat.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 bg-white/5 rounded border border-white/5"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <div className="flex items-center justify-between pt-3 border-t border-white/5 text-xs">
                  <span className="text-slate-400 font-medium">Feature Highlights</span>
                  <span className="font-semibold text-orange-400">{feat.highlight}</span>
                </div>
              </div>

              <Link href={feat.link} className="w-full">
                <Button
                  variant={feat.category === "transport" ? "primary" : "secondary"}
                  className="w-full py-2.5 text-xs font-bold"
                >
                  {feat.btnText}
                </Button>
              </Link>
            </div>
          </div>
        ))}
      </div>

      {/* CTA section */}
      <div className="glass-panel rounded-2xl p-8 border-white/5 shadow-2xl relative overflow-hidden text-center mt-6">
        <div className="absolute -top-24 -left-24 h-48 w-48 rounded-full bg-blue-500/10 blur-[80px]" />
        <div className="absolute -bottom-24 -right-24 h-48 w-48 rounded-full bg-orange-500/10 blur-[80px]" />
        
        <h2 className="text-2xl font-bold text-white mb-3 tracking-tight">Ready to start your journey?</h2>
        <p className="text-slate-400 text-sm max-w-lg mx-auto mb-6 leading-relaxed">
          Book your bus, train, or flight ticket with instant seat lock and secure mobile payment gateways in Pakistan.
        </p>
        
        <div className="flex justify-center">
          <Link href="/">
            <Button className="px-7 py-3 text-base">
              Search & Book Now
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

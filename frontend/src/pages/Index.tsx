
import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import Navbar from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { ArrowRight, Play } from "lucide-react";

const Index = () => {
  const { isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-background page-transition">
      <Navbar />
      
      <main className="container px-4 pt-32 pb-16 md:py-32">
        <section className="max-w-5xl mx-auto text-center">
          <h1 className="hero-heading bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/80">
            Your Personal Video Experience
          </h1>
          
          <p className="hero-subheading mx-auto">
            Personalized, adaptive, and seamless video streaming powered by advanced technology.
            Dive into a world of curated content tailored just for you.
          </p>
          
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            {isAuthenticated ? (
              <Button asChild size="lg" className="group">
                <Link to="/dashboard">
                  Go to Dashboard
                  <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </Link>
              </Button>
            ) : (
              <>
                <Button asChild size="lg" className="group">
                  <Link to="/register">
                    Get Started
                    <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg">
                  <Link to="/login">Login</Link>
                </Button>
              </>
            )}
          </div>
        </section>

        <section className="mt-32 max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-card p-6 rounded-lg shadow-sm border border-border">
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <Play className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Seamless Streaming</h3>
              <p className="text-muted-foreground">
                Enjoy uninterrupted video playback with adaptive quality based on
                your network conditions.
              </p>
            </div>
            
            <div className="bg-card p-6 rounded-lg shadow-sm border border-border">
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <svg className="h-6 w-6 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">Personalized For You</h3>
              <p className="text-muted-foreground">
                Our intelligent system learns your preferences and curates
                content tailored specifically to your interests.
              </p>
            </div>
            
            <div className="bg-card p-6 rounded-lg shadow-sm border border-border">
              <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <svg className="h-6 w-6 text-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold mb-2">Secure & Private</h3>
              <p className="text-muted-foreground">
                Your data and viewing preferences are secured with industry-leading
                encryption and privacy measures.
              </p>
            </div>
          </div>
        </section>
      </main>
      
      <footer className="border-t border-border py-6 px-4">
        <div className="container mx-auto flex flex-col md:flex-row justify-between items-center">
          <p className="text-sm text-muted-foreground">
            © 2023 StreamSync. All rights reserved.
          </p>
          <div className="flex space-x-6 mt-4 md:mt-0">
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
              Terms
            </a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
              Privacy
            </a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
              Contact
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;

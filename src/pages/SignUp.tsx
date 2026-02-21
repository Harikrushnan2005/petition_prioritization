import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Mail, Lock } from "lucide-react";
const SignUp = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();
  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      toast({ title: "Error", description: "Passwords do not match", variant: "destructive" });
      return;
    }
    setIsLoading(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:5000"}/api/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (response.ok) {
        toast({ title: "Account created!", description: "You can now log in." });
        navigate("/login");
      } else {
        toast({ title: "Sign up failed", description: data.error, variant: "destructive" });
      }
    } catch {
      toast({ title: "Error", description: "Failed to connect to server", variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };
  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      <div
        className="absolute inset-0 z-0"
        style={{
          background: "linear-gradient(135deg, hsl(200 100% 60%) 0%, hsl(260 90% 60%) 50%, hsl(320 85% 60%) 100%)",
        }}
      />
      <div className="relative z-10 bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md mx-4">
        <h1 className="text-3xl font-bold text-center mb-8 text-foreground">Sign Up</h1>
        <form onSubmit={handleSignUp} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="email" className="text-sm font-medium text-foreground">Email</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                id="email"
                type="email"
                placeholder="Type your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="pl-10 bg-white border-b-2 border-t-0 border-x-0 border-input rounded-none focus-visible:border-primary focus-visible:ring-0"
                required
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="password" className="text-sm font-medium text-foreground">Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                id="password"
                type="password"
                placeholder="Type your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-10 bg-white border-b-2 border-t-0 border-x-0 border-input rounded-none focus-visible:border-primary focus-visible:ring-0"
                required
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirmPassword" className="text-sm font-medium text-foreground">Confirm Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="pl-10 bg-white border-b-2 border-t-0 border-x-0 border-input rounded-none focus-visible:border-primary focus-visible:ring-0"
                required
              />
            </div>
          </div>
          <Button
            type="submit"
            disabled={isLoading}
            className="w-full h-12 text-base font-semibold rounded-full"
            style={{
              background: "linear-gradient(90deg, hsl(180 85% 50%) 0%, hsl(260 75% 60%) 100%)",
            }}
          >
            {isLoading ? "Signing up..." : "SIGN UP"}
          </Button>
        </form>
        <div className="mt-8 text-center">
          <p className="text-sm text-muted-foreground mb-2">Already have an account?</p>
          <button
            onClick={() => navigate("/login")}
            className="text-sm font-semibold text-foreground hover:text-primary transition-colors"
          >
            LOGIN
          </button>
        </div>
      </div>
    </div>
  );
};
export default SignUp;
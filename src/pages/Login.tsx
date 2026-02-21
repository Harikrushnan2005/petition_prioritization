import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { User, Lock } from "lucide-react";

const Login = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:5000"}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok) {
        sessionStorage.setItem("isLoggedIn", "true");
        sessionStorage.setItem("username", data.username);
        sessionStorage.setItem("userRole", data.role);
        sessionStorage.setItem("userDepartment", data.department || '');
        toast({
          title: "Login successful!",
          description: `Welcome back, ${data.username}`,
        });
        navigate("/");
      } else {
        toast({
          title: "Login failed",
          description: data.error,
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to connect to server",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden">
      {/* Gradient background */}
      <div
        className="absolute inset-0 z-0"
        style={{
          background: "linear-gradient(135deg, hsl(200 100% 60%) 0%, hsl(260 90% 60%) 50%, hsl(320 85% 60%) 100%)"
        }}
      />

      {/* Login card */}
      <div className="relative z-10 bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md mx-4">
        <h1 className="text-3xl font-bold text-center mb-8 text-foreground">Login</h1>

        <form onSubmit={handleLogin} className="space-y-6">
          {/* Username field */}
          <div className="space-y-2">
            <Label htmlFor="username" className="text-sm font-medium text-foreground">
              Username
            </Label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-4 h-4" />
              <Input
                id="username"
                type="text"
                placeholder="Type your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="pl-10 bg-white border-b-2 border-t-0 border-x-0 border-input rounded-none focus-visible:border-primary focus-visible:ring-0"
                required
              />
            </div>
          </div>

          {/* Password field */}
          <div className="space-y-2">
            <Label htmlFor="password" className="text-sm font-medium text-foreground">
              Password
            </Label>
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

          {/* Forgot password link */}
          <div className="text-right">
            <button
              type="button"
              onClick={() => navigate("/forgot-password")}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Forgot password?
            </button>
          </div>

          {/* Login button */}
          <Button
            type="submit"
            disabled={isLoading}
            className="w-full h-12 text-base font-semibold rounded-full"
            style={{
              background: "linear-gradient(90deg, hsl(180 85% 50%) 0%, hsl(260 75% 60%) 100%)",
            }}
          >
            {isLoading ? "Logging in..." : "LOGIN"}
          </Button>
        </form>


        {/* Sign up link */}
        <div className="mt-8 text-center">
          <p className="text-sm text-muted-foreground mb-2">Don't have an account?</p>
          <button
            onClick={() => navigate("/signup")}
            className="text-sm font-semibold text-foreground hover:text-primary transition-colors"
          >
            SIGN UP
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;

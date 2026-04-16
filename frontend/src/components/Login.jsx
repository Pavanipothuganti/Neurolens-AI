import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../api";

const Login = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      await login(username, password);
      navigate("/");
    } catch (err) {
      setError(err.message || "Invalid credentials. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="glass-panel auth-card">
        <h1 className="brand-title" style={{ textAlign: "center", marginBottom: "8px" }}>NeuroLens AI</h1>
        <p style={{ textAlign: "center", color: "var(--text-muted)", marginBottom: "32px" }}>
          Secure Clinical Portal Login
        </p>

        {error && <div className="error-msg" style={{ marginBottom: "20px" }}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              className="form-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your clinical ID"
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "16px" }} disabled={isLoading}>
            {isLoading ? "Authenticating..." : "Login to Workspace"}
          </button>
        </form>

        <div style={{ marginTop: "24px", textAlign: "center", fontSize: "0.9rem", color: "var(--text-muted)" }}>
          Don't have an account? <Link to="/signup" style={{ color: "var(--primary)", fontWeight: "600", textDecoration: "none" }}>Sign Up</Link>
        </div>
      </div>
    </div>
  );
};

export default Login;

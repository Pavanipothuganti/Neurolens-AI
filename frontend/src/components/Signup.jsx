import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { signup } from "../api";

const Signup = () => {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      await signup(username, email, password);
      navigate("/");
    } catch (err) {
      setError(err.message || "Could not register account. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="glass-panel auth-card">
        <h1 className="brand-title" style={{ textAlign: "center", marginBottom: "8px" }}>NeuroLens AI</h1>
        <p style={{ textAlign: "center", color: "var(--text-muted)", marginBottom: "32px" }}>
          Neurodiagnostic Portal Registration
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
              placeholder="clinical_id_101"
              required
            />
          </div>

          <div className="form-group">
            <label>Email Address</label>
            <input
              type="email"
              className="form-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="dr.name@hospital.com"
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

          <div className="form-group">
            <label>Confirm Password</label>
            <input
              type="password"
              className="form-input"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: "100%", marginTop: "16px" }} disabled={isLoading}>
            {isLoading ? "Registering..." : "Create Clinical Account"}
          </button>
        </form>

        <div style={{ marginTop: "24px", textAlign: "center", fontSize: "0.9rem", color: "var(--text-muted)" }}>
          Already have an account? <Link to="/login" style={{ color: "var(--primary)", fontWeight: "600", textDecoration: "none" }}>Login here</Link>
        </div>
      </div>
    </div>
  );
};

export default Signup;

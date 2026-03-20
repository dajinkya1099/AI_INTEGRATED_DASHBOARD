import { useState } from "react";
import { loginUser } from "../Service/api";
import { useNavigate } from "react-router-dom";
import "../Styles/auth.css";

function Login({ setUser }) {
    const [form, setForm] = useState({
        username: "",
        password: ""
    });

    const navigate = useNavigate();

    const handleLogin = async () => {
        const res = await loginUser(form);

        if (res.success) {
            localStorage.setItem("token", res.token);
            localStorage.setItem("user", JSON.stringify(res.user));
            setUser(res.user);
            navigate("/");
        } else {
            alert("Invalid credentials");
        }
    };

    return (
        <div className="auth-container">

            <div className="auth-title">
                <h1>AI Integrated Dashboard</h1>
                <p>Smart insights powered by AI</p>
            </div>
            <div className="auth-card">
                <h2>Login</h2>

                <input
                    className="auth-input"
                    placeholder="Username"
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                />

                <input
                    className="auth-input"
                    type="password"
                    placeholder="Password"
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                />

                <button className="auth-btn" onClick={handleLogin}>
                    Login
                </button>

                <p className="auth-link" onClick={() => navigate("/signup")}>
                    Don't have account? Signup
                </p>
            </div>
        </div>
    );
}

export default Login;
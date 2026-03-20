// import { useState } from "react";
// import { signupUser } from "../Service/api";
// import { useNavigate } from "react-router-dom";
// import "../Styles/auth.css";

// function Signup() {
//     const [form, setForm] = useState({
//         email: "",
//         username: "",
//         password: "",
//         role: "user"
//     });

//     const navigate = useNavigate();

//     const handleSignup = async () => {
//         const res = await signupUser(form);

//         if (res.success) {
//             alert("Signup successful");
//             navigate("/login");
//         } else {
//             alert("Signup failed");
//         }
//     };

//     return (
//         <div className="auth-container">
//             <div className="auth-title">
//                 <h1>AI Integrated Dashboard</h1>
//                 <p>Create your account to get started</p>
//             </div>
//             <div className="auth-card">
//                 <h2>Signup</h2>

//                 <input
//                     className="auth-input"
//                     placeholder="Email"
//                     onChange={(e) => setForm({ ...form, email: e.target.value })}
//                 />

//                 <input
//                     className="auth-input"
//                     placeholder="Username"
//                     onChange={(e) => setForm({ ...form, username: e.target.value })}
//                 />

//                 <input
//                     className="auth-input"
//                     type="password"
//                     placeholder="Password"
//                     onChange={(e) => setForm({ ...form, password: e.target.value })}
//                 />

//                 {/* <select
//           className="auth-input"
//           onChange={(e) => setForm({ ...form, role: e.target.value })}
//         >
//           <option value="USER">User</option>
//           <option value="ADMIN">Admin</option>
//         </select> */}

//                 <button className="auth-btn" onClick={handleSignup}>
//                     Signup
//                 </button>

//                 <p className="auth-link" onClick={() => navigate("/login")}>
//                     Already have account? Login
//                 </p>
//             </div>
//         </div>
//     );
// }

// export default Signup;

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../Styles/auth.css";

function Signup() {

  const [form, setForm] = useState({
    email: "",
    username: "",
    password: "",
    role: "USER"
  });

  const [otp, setOtp] = useState("");
  const [step, setStep] = useState(1);
  const [timer, setTimer] = useState(0);

  const navigate = useNavigate();

  // ⏳ Timer countdown
  useEffect(() => {
    let interval;

    if (timer > 0) {
      interval = setInterval(() => {
        setTimer((prev) => prev - 1);
      }, 1000);
    }

    return () => clearInterval(interval);
  }, [timer]);

  // 🔹 Send OTP
  const handleSendOtp = async () => {
    const res = await fetch("http://localhost:8282/send-otp", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email: form.email })
    });

    if (res.ok) {
      alert("OTP sent to email");
      setStep(2);
      setTimer(60);
    } else {
      alert("Failed to send OTP");
    }
  };

  // 🔹 Verify OTP + Signup
  const handleVerifyOtp = async () => {
    const res = await fetch("http://localhost:8282/verify-otp-signup", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        ...form,
        otp
      })
    });

    const data = await res.json();

    if (data.success) {
      alert("Signup successful");
      navigate("/login");
    } else {
      alert(data.detail || "Invalid OTP");
    }
  };

  // 🔹 Resend OTP
  const handleResendOtp = async () => {
    await fetch("http://localhost:8282/resend-otp", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email: form.email })
    });

    setTimer(60);
  };

  return (
    <div className="auth-container">

      {/* Heading */}
      <div className="auth-title">
        <h1>AI Integrated Dashboard</h1>
        <p>Create your account to get started</p>
      </div>

      <div className="auth-card">
        <h2>Signup</h2>

        {/* STEP 1 - USER DETAILS */}
        {step === 1 && (
          <>
            <input
              className="auth-input"
              placeholder="Email"
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />

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

            <button className="auth-btn" onClick={handleSendOtp}>
              Send OTP
            </button>
          </>
        )}

        {/* STEP 2 - OTP */}
        {step === 2 && (
          <>
            <input
              className="auth-input"
              placeholder="Enter OTP"
              onChange={(e) => setOtp(e.target.value)}
            />

            <button className="auth-btn" onClick={handleVerifyOtp}>
              Verify & Signup
            </button>

            {/* TIMER / RESEND */}
            {timer > 0 ? (
              <p style={{ textAlign: "center" }}>
                Resend OTP in {timer}s
              </p>
            ) : (
              <p
                className="auth-link"
                onClick={handleResendOtp}
              >
                Resend OTP
              </p>
            )}
          </>
        )}

        <p className="auth-link" onClick={() => navigate("/login")}>
          Already have account? Login
        </p>

      </div>
    </div>
  );
}

export default Signup;
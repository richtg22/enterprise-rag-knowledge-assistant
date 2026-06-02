import { useState } from "react";
import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

function AuthPage({ setToken }) {
  const [isLogin, setIsLogin] = useState(true);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const register = async () => {
    try {
      await axios.post(`${API_BASE_URL}/register`, {
        name,
        email,
        password,
      });

      alert("Registration successful");
      setIsLogin(true);
    } catch (error) {
      alert(error.response?.data?.detail || "Registration failed");
    }
  };

  const login = async () => {
    try {
      const formData = new FormData();

      formData.append("username", email);
      formData.append("password", password);

      const response = await axios.post(
        `${API_BASE_URL}/login`,
        formData
      );

      localStorage.setItem(
        "token",
        response.data.access_token
      );

      setToken(response.data.access_token);

      alert("Login successful");
    } catch (error) {
      alert(error.response?.data?.detail || "Login failed");
    }
  };

  return (
    <div className="auth-container">
      <h2>{isLogin ? "Login" : "Register"}</h2>

      {!isLogin && (
        <input
          type="text"
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      )}

      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      <button
        onClick={isLogin ? login : register}
      >
        {isLogin ? "Login" : "Register"}
      </button>

      <p>
        {isLogin
          ? "Don't have an account?"
          : "Already have an account?"}
      </p>

      <button
        onClick={() => setIsLogin(!isLogin)}
      >
        Switch
      </button>
    </div>
  );
}

export default AuthPage;
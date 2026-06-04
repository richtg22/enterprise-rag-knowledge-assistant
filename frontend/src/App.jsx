import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE_URL = "https://enterprise-rag-knowledge-assistant.onrender.com";

function App() {
  const [isLogin, setIsLogin] = useState(true);
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [files, setFiles] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [documentsLoaded, setDocumentsLoaded] = useState(false);

  const [question, setQuestion] = useState("");
  const [chatHistory, setChatHistory] = useState([]);

  const [loading, setLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");

  useEffect(() => {
    const savedUser = localStorage.getItem("user");

    if (savedUser && token) {
      setUser(JSON.parse(savedUser));
      loadDocuments();
    }
  }, [token]);

  const authHeaders = () => ({
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });

  const handleRegister = async () => {
    try {
      await axios.post(`${API_BASE_URL}/register`, {
        name,
        email,
        password,
      });

      alert("Registration successful. Please login.");
      setIsLogin(true);
    } catch (error) {
      console.error(error);
      alert(error.response?.data?.detail || "Registration failed");
    }
  };

  const handleLogin = async () => {
    try {
      const formData = new URLSearchParams();
      formData.append("username", email);
      formData.append("password", password);

      const response = await axios.post(
        `${API_BASE_URL}/login`,
        formData,
        {
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
        }
      );

      localStorage.setItem("token", response.data.access_token);
      localStorage.setItem("user", JSON.stringify(response.data.user));

      setToken(response.data.access_token);
      setUser(response.data.user);

      setEmail("");
      setPassword("");

      await loadDocuments();
    } catch (error) {
      console.error(error);
      alert(error.response?.data?.detail || "Login failed");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");

    setToken(null);
    setUser(null);
    setFiles([]);
    setDocuments([]);
    setDocumentsLoaded(false);
    setChatHistory([]);
    setUploadMessage("");
  };

  const handleFileChange = (event) => {
    setFiles(Array.from(event.target.files));
  };

  const uploadDocuments = async () => {
    if (files.length === 0) {
      alert("Please select at least one PDF file.");
      return;
    }

    try {
      setLoading(true);

      const formData = new FormData();

      files.forEach((file) => {
        formData.append("files", file);
      });

      const response = await axios.post(
        `${API_BASE_URL}/upload`,
        formData,
        {
          ...authHeaders(),
          headers: {
            ...authHeaders().headers,
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setDocumentsLoaded(true);
      setUploadMessage(
        `✓ ${response.data.documents} document(s) uploaded successfully\n✓ ${response.data.chunks} chunks indexed`
      );

      await loadDocuments();
    } catch (error) {
      console.error(error);
      alert(error.response?.data?.detail || "Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  const loadDocuments = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/documents`,
        authHeaders()
      );

      setDocuments(response.data);

      if (response.data.length > 0) {
        setDocumentsLoaded(true);
      }
    } catch (error) {
      console.error(error);
    }
  };

  const deleteDocument = async (documentId) => {
    const confirmDelete = window.confirm(
      "Are you sure you want to delete this document?"
    );

    if (!confirmDelete) return;

    try {
      await axios.delete(
        `${API_BASE_URL}/documents/${documentId}`,
        authHeaders()
      );

      await loadDocuments();

      alert("Document deleted successfully.");
    } catch (error) {
      console.error(error);
      alert(error.response?.data?.detail || "Failed to delete document.");
    }
  };

  const clearKnowledgeBase = async () => {
    const confirmClear = window.confirm(
      "Are you sure you want to clear your full knowledge base?"
    );

    if (!confirmClear) return;

    try {
      await axios.delete(
        `${API_BASE_URL}/clear`,
        authHeaders()
      );

      setFiles([]);
      setDocuments([]);
      setDocumentsLoaded(false);
      setChatHistory([]);
      setUploadMessage("");

      alert("Knowledge base cleared successfully.");
    } catch (error) {
      console.error(error);
      alert(error.response?.data?.detail || "Failed to clear knowledge base.");
    }
  };

  const askQuestion = async () => {
    if (!question.trim()) {
      alert("Please enter a question.");
      return;
    }

    try {
      setLoading(true);

      const response = await axios.post(
        `${API_BASE_URL}/ask`,
        {
          question,
        },
        authHeaders()
      );

      const newChat = {
        question,
        answer: response.data.answer,
        sources: response.data.sources || [],
        timestamp: new Date().toLocaleTimeString(),
      };

      setChatHistory((previous) => [...previous, newChat]);
      setQuestion("");
    } catch (error) {
      console.error(error);
      alert(error.response?.data?.detail || "Failed to get answer.");
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="app">
        <h1>Enterprise RAG Knowledge Assistant</h1>

        <section className="card auth-card">
          <h2>{isLogin ? "Login" : "Register"}</h2>

          {!isLogin && (
            <input
              type="text"
              placeholder="Name"
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          )}

          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />

          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />

          <button onClick={isLogin ? handleLogin : handleRegister}>
            {isLogin ? "Login" : "Register"}
          </button>

          <p>
            {isLogin
              ? "Don't have an account?"
              : "Already have an account?"}
          </p>

          <button onClick={() => setIsLogin(!isLogin)}>
            Switch
          </button>
        </section>
      </div>
    );
  }

  return (
    <div className="app">
      <h1>Enterprise RAG Knowledge Assistant</h1>

      <button onClick={handleLogout}>Logout</button>

      <p>
        Upload enterprise documents and ask grounded questions with source
        citations.
      </p>

      <section className="card">
        <h2>Upload Document</h2>

        <input
          type="file"
          multiple
          accept="application/pdf"
          onChange={handleFileChange}
        />

        {files.length > 0 && (
          <div>
            <h3>Selected Files ({files.length})</h3>
            {files.map((file, index) => (
              <p key={index}>• {file.name}</p>
            ))}
          </div>
        )}

        <div className="action-buttons">
          <button className="upload-btn"
          onClick={uploadDocuments}
          disabled={loading}
          >
            {loading ? "Uploading..." : "📤 Upload & Index"}
          </button>
          
          <button className="clear-btn"
          onClick={clearKnowledgeBase}
          >
            🗑 Clear Knowledge Base
          </button>
        </div>

        {uploadMessage && (
          <pre className="success-message">{uploadMessage}</pre>
        )}
      </section>

      <section className="card">
        <h2>My Documents</h2>

        {documents.length === 0 ? (
          <p>No documents uploaded yet.</p>
        ) : (
          documents.map((document) => (
            <div key={document.id} className="document-item">
              <span>📄 {document.filename}</span>

              <button onClick={() => deleteDocument(document.id)}>
                Delete
              </button>
            </div>
          ))
        )}
      </section>

      <section className="card">
        <h2>Ask a Question</h2>

        <textarea
          placeholder="Ask something about the uploaded document..."
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
        />

        <button
          onClick={askQuestion}
          disabled={!documentsLoaded || loading}
        >
          {loading ? "Thinking..." : "Ask"}
        </button>

        {!documentsLoaded && (
          <p className="helper-text">
            Please upload and index documents before asking questions.
          </p>
        )}
      </section>

      <section className="card">
        <h2>Chat History</h2>

        {chatHistory.length === 0 ? (
          <p className="empty-chat">
            No conversations yet. Upload documents and ask your first question.
          </p>
        ) : (
          chatHistory.map((chat, index) => (
            <div key={index} className="chat-item">
              <div className="chat-bubble user">
                <strong>You</strong>
                <p>{chat.question}</p>
              </div>

              <div className="chat-bubble assistant">
                <strong>Assistant</strong>
                <p>{chat.answer}</p>
                <small>{chat.timestamp}</small>
              </div>

              {chat.sources.length > 0 && (
                <div className="sources">
                  <h3>Sources</h3>

                  {chat.sources.map((source, sourceIndex) => (
                    <div key={sourceIndex} className="source">
                      <span>{source.source}</span>
                      <span>Page: {source.page}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </section>
    </div>
  );
}

export default App;
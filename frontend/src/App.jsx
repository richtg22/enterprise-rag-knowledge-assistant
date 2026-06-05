import { useEffect, useRef, useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE_URL = "https://enterprise-rag-knowledge-assistant.onrender.com";
// const API_BASE_URL = "http://127.0.0.1:8000";

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

  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);

  const [loading, setLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");

  const fileInputRef = useRef(null);

  const authHeaders = () => ({
    headers: {
      Authorization: `Bearer ${localStorage.getItem("token")}`,
    },
  });

  useEffect(() => {
    const savedUser = localStorage.getItem("user");

    if (savedUser && token) {
      setUser(JSON.parse(savedUser));
      loadDocuments();
      loadConversations();
    }
  }, [token]);

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

      const response = await axios.post(`${API_BASE_URL}/login`, formData, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      localStorage.setItem("token", response.data.access_token);
      localStorage.setItem("user", JSON.stringify(response.data.user));

      setToken(response.data.access_token);
      setUser(response.data.user);

      setEmail("");
      setPassword("");

      await loadDocuments();
      await loadConversations();
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
    setConversations([]);
    setActiveConversationId(null);
    setUploadMessage("");
  };

  const loadDocuments = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/documents`, authHeaders());
      setDocuments(response.data);
      setDocumentsLoaded(response.data.length > 0);
    } catch (error) {
      console.error(error);
    }
  };

  const loadConversations = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/conversations`, authHeaders());
      setConversations(response.data);

      if (response.data.length > 0 && !activeConversationId) {
        const firstConversation = response.data[0];
        setActiveConversationId(firstConversation.id);
        await loadConversationChats(firstConversation.id);
      }
    } catch (error) {
      console.error(error);
    }
  };

  const loadConversationChats = async (conversationId) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/conversations/${conversationId}/chats`,
        authHeaders()
      );

      const formattedChats = response.data.map((chat) => ({
        question: chat.question,
        answer: chat.answer,
        sources: chat.sources || [],
        timestamp: new Date(chat.created_at).toLocaleTimeString(),
      }));

      setChatHistory(formattedChats);
      setActiveConversationId(conversationId);
    } catch (error) {
      console.error(error);
    }
  };

  const createNewConversation = async () => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/conversations`,
        { title: "New Conversation" },
        authHeaders()
      );

      setConversations((previous) => [response.data, ...previous]);
      setActiveConversationId(response.data.id);
      setChatHistory([]);
    } catch (error) {
      console.error(error);
      alert("Failed to create conversation.");
    }
  };

  const deleteConversation = async (conversationId) => {
    const confirmDelete = window.confirm("Delete this conversation?");

    if (!confirmDelete) return;

    try {
      await axios.delete(
        `${API_BASE_URL}/conversations/${conversationId}`,
        authHeaders()
      );

      const updatedConversations = conversations.filter(
        (conversation) => conversation.id !== conversationId
      );

      setConversations(updatedConversations);

      if (activeConversationId === conversationId) {
        setChatHistory([]);

        if (updatedConversations.length > 0) {
          setActiveConversationId(updatedConversations[0].id);
          await loadConversationChats(updatedConversations[0].id);
        } else {
          setActiveConversationId(null);
        }
      }
    } catch (error) {
      console.error(error);
      alert("Failed to delete conversation.");
    }
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

      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          ...authHeaders().headers,
          "Content-Type": "multipart/form-data",
        },
      });

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

  const viewDocument = async (documentId) => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/documents/${documentId}/view`,
      authHeaders()
    );

    window.open(response.data.url, "_blank");
  } catch (error) {
    console.error(error);
    alert(error.response?.data?.detail || "Failed to open document.");
  }
};

  const deleteDocument = async (documentId) => {
    const confirmDelete = window.confirm("Are you sure you want to delete this document?");

    if (!confirmDelete) return;

    try {
      await axios.delete(`${API_BASE_URL}/documents/${documentId}`, authHeaders());

      await loadDocuments();

      setFiles([]);
      setUploadMessage("");

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

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
      await axios.delete(`${API_BASE_URL}/clear`, authHeaders());

      setFiles([]);
      setDocuments([]);
      setDocumentsLoaded(false);
      setChatHistory([]);
      setConversations([]);
      setActiveConversationId(null);
      setUploadMessage("");

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

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
          conversation_id: activeConversationId,
        },
        authHeaders()
      );

      const conversationId = response.data.conversation_id;

      await loadConversations();

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
      <div className="auth-page">
        <div className="auth-card">
          <h1>Enterprise RAG</h1>
          <p>Secure document Q&A with source-grounded answers.</p>

          <h2>{isLogin ? "Login" : "Create account"}</h2>

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

          <button className="primary-btn" onClick={isLogin ? handleLogin : handleRegister}>
            {isLogin ? "Login" : "Register"}
          </button>

          <button className="link-btn" onClick={() => setIsLogin(!isLogin)}>
            {isLogin ? "Create a new account" : "Already have an account? Login"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div>
          <h2>Enterprise RAG</h2>
          <p className="sidebar-user">{user.email}</p>

          <button className="new-chat-btn" onClick={createNewConversation}>
            + New Chat
          </button>

          <h3>Conversations</h3>

          <div className="conversation-list">
            {conversations.length === 0 ? (
              <p className="muted">No conversations yet.</p>
            ) : (
              conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  className={`conversation-item ${
                    activeConversationId === conversation.id ? "active" : ""
                  }`}
                >
                  <button
                    onClick={() => loadConversationChats(conversation.id)}
                    className="conversation-title"
                  >
                    {conversation.title}
                  </button>

                  <button
                    className="delete-conversation-btn"
                    onClick={() => deleteConversation(conversation.id)}
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        <button className="logout-btn" onClick={handleLogout}>
          Logout
        </button>
      </aside>

      <main className="main-content">
        <section className="hero">
          <h1>Enterprise RAG Knowledge Assistant</h1>
          <p>Upload enterprise documents and ask grounded questions with source citations.</p>
        </section>

        <section className="card">
          <h2>Upload Document</h2>

          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="application/pdf"
            onChange={handleFileChange}
          />

          {files.length > 0 && (
            <div className="selected-files">
              <h3>Selected Files ({files.length})</h3>
              {files.map((file, index) => (
                <p key={index}>• {file.name}</p>
              ))}
            </div>
          )}

          <div className="action-buttons">
            <button className="upload-btn" onClick={uploadDocuments} disabled={loading}>
              {loading ? "Uploading..." : "📤 Upload & Index"}
            </button>

            <button className="clear-btn" onClick={clearKnowledgeBase}>
              🗑 Clear Knowledge Base
            </button>
          </div>

          {uploadMessage && <pre className="success-message">{uploadMessage}</pre>}
        </section>

        <section className="card">
          <h2>My Documents</h2>

          {documents.length === 0 ? (
            <p className="muted">No documents uploaded yet.</p>
          ) : (
            documents.map((document) => (
              <div key={document.id} className="document-item">
                <span>📄 {document.filename}</span>

                <div className="document-actions">
                  <button 
                    className="small-view-btn"
                    onClick={() => viewDocument(document.id)}
                    >
                      View
                    </button>
                    <button
                      className="small-danger-btn"
                      onClick={() => deleteDocument(document.id)}
                    >
                      Delete
                    </button>
                </div>
              </div>
            ))
          )}
        </section>

        <section className="card">
          <h2>Ask a Question</h2>

          <textarea
            placeholder="Ask something about the uploaded documents..."
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />

          <button
            className="primary-btn"
            onClick={askQuestion}
            disabled={!documentsLoaded || loading}
          >
            {loading ? "Thinking..." : "Ask"}
          </button>

          {!documentsLoaded && (
            <p className="helper-text">Please upload and index documents before asking questions.</p>
          )}
        </section>

        <section className="card">
          <h2>Current Conversation</h2>

          {chatHistory.length === 0 ? (
            <p className="empty-chat">No messages yet. Ask your first question.</p>
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
      </main>
    </div>
  );
}

export default App;
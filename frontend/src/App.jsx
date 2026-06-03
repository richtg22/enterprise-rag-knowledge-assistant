import { useRef, useState } from "react";
import axios from "axios";
import "./App.css";
import AuthPage from "./components/AuthPage";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [documents, setDocuments] = useState(0);
  const [chunks, setChunks] = useState(0);
  const [documentsLoaded, setDocumentsLoaded] = useState(false);
  const [token, setToken] = useState(localStorage.getItem("token"));

  const fileInputRef = useRef(null);

  if (!token) {
    return <AuthPage setToken={setToken} />;
  }

  const uploadDocument = async () => {
    const token=localStorage.getItem("token");

    if (!file || file.length === 0) {
      alert("Please select at least one PDF.");
      return;
    }

    const formData = new FormData();

    for (let i = 0; i < file.length; i++) {
      formData.append("files", file[i]);
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload`, formData,
        {
          headers:{
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setDocuments(response.data.documents);
      setChunks(response.data.chunks);
      setDocumentsLoaded(true);
    } catch (error) {
      console.error(error);
      alert(error.response?.data?.detail || "Upload failed.");
    } finally {
      setLoading(false);
    }
  };

  const askQuestion = async () => {
    if (!question.trim()) {
      alert("Please enter a question.");
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/ask`, {
        question,
      },
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

      const newChat = {
        question,
        answer: response.data.answer,
        sources: response.data.sources || [],
        timestamp: new Date().toLocaleTimeString(),
      };

      setChatHistory((prev) => [...prev, newChat]);
      setQuestion("");
    } catch (error) {
      console.error(error);
      alert("Question failed.");
    } finally {
      setLoading(false);
    }
  };

  const clearKnowledgeBase = async () => {    
    setLoading(true);
    
    try {
      await axios.delete(`${API_BASE_URL}/clear`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      resetDashboardState();
      
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      
      alert("Knowledge base cleared successfully.");
    } catch (error) {
      console.error(error);
      alert(error.response?.data?.detail || "Failed to clear knowledge base.");
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    resetDashboardState();
    setToken(null);
  };

  const resetDashboardState = () => {
    setFile(null);
    setQuestion("");
    setChatHistory([]);
    setDocuments(0);
    setChunks(0);
    setDocumentsLoaded(false);
    
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="container">
      <h1>Enterprise RAG Knowledge Assistant</h1>
      <button onClick={logout}>
        Logout
      </button>
      <p>
        Upload enterprise documents and ask grounded questions with source
        citations.
      </p>

      <section className="card">
        <h2>Upload Document</h2>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files)}
        />

        {file && (
          <div className="selected-files">
            <p>
              <strong>Selected Files ({file.length})</strong>
            </p>

            {Array.from(file).map((f, index) => (
              <div key={index}>• {f.name}</div>
            ))}
          </div>
        )}

        <div className="button-group">
          <button onClick={uploadDocument} disabled={loading}>
            {loading ? "Indexing..." : "Upload & Index"}
          </button>

          <button onClick={clearKnowledgeBase} disabled={loading}>
            Clear Knowledge Base
          </button>
        </div>

        {documentsLoaded && (
          <div className="success-message">
            <div>✓ {documents} document(s) uploaded successfully</div>
            <div>✓ {chunks} chunks indexed</div>
          </div>
        )}
      </section>

      <section className="card">
        <h2>Ask a Question</h2>

        <textarea
          placeholder="Ask something about the uploaded document..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />

        <button onClick={askQuestion} disabled={!documentsLoaded || loading}>
          {loading ? "Thinking..." : "Ask"}
        </button>

        {!documentsLoaded && (
          <p className="helper-text">
            Please click "Upload & Index" before asking questions.
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
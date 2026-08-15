(function (window) {
  const API_BASE = ""; // Relative path to current domain/port

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  async function request(endpoint, options = {}) {
    const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;
    const headers = options.headers || {};

    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const csrfToken = getCookie("csrftoken");
    if (csrfToken) {
      headers["X-CSRFToken"] = csrfToken;
    }

    const config = {
      method: options.method || "GET",
      headers: headers,
      credentials: "include", // Enable Django session cookies
      ...options
    };

    if (config.body && typeof config.body === "object" && !(config.body instanceof FormData)) {
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(url, config);
      const text = await response.text();
      let data = {};
      try {
        data = JSON.parse(text);
      } catch {
        data = { message: text && !text.startsWith("<!") ? text : `Server Error (Status ${response.status})` };
      }

      if (!response.ok || data.status === "error") {
        const errorMsg = data.message || `Request failed with status ${response.status}`;
        const error = new Error(errorMsg);
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (err) {
      console.error(`[API Error] ${config.method} ${url}:`, err);
      throw err;
    }
  }

  const STORAGE_KEY_USER = "lumina.user";
  const STORAGE_KEY_MATERIAL = "lumina.currentMaterial";
  const STORAGE_KEY_CONCEPTS = "lumina.selectedConcepts";

  const API = {
    storage: {
      getUser() {
        try {
          const raw = localStorage.getItem(STORAGE_KEY_USER);
          return raw ? JSON.parse(raw) : null;
        } catch {
          return null;
        }
      },
      setUser(user) {
        try {
          localStorage.setItem(STORAGE_KEY_USER, JSON.stringify(user));
        } catch (e) {
          console.error("Failed to save user in localStorage", e);
        }
      },
      clearUser() {
        try {
          localStorage.removeItem(STORAGE_KEY_USER);
        } catch (e) {
          console.error("Failed to clear user from localStorage", e);
        }
      },
      getMaterial() {
        try {
          const raw = localStorage.getItem(STORAGE_KEY_MATERIAL);
          return raw ? JSON.parse(raw) : null;
        } catch {
          return null;
        }
      },
      setMaterial(materialData) {
        try {
          localStorage.setItem(STORAGE_KEY_MATERIAL, JSON.stringify(materialData));
        } catch (e) {
          console.error("Failed to save material in localStorage", e);
        }
      },
      clearMaterial() {
        try {
          localStorage.removeItem(STORAGE_KEY_MATERIAL);
          localStorage.removeItem(STORAGE_KEY_CONCEPTS);
        } catch (e) {
          console.error("Failed to clear material from localStorage", e);
        }
      },
      getSelectedConcepts() {
        try {
          const raw = localStorage.getItem(STORAGE_KEY_CONCEPTS);
          return raw ? JSON.parse(raw) : [];
        } catch {
          return [];
        }
      },
      setSelectedConcepts(concepts) {
        try {
          localStorage.setItem(STORAGE_KEY_CONCEPTS, JSON.stringify(concepts));
        } catch (e) {
          console.error("Failed to save selected concepts in localStorage", e);
        }
      },
      getLearningPath() {
        try {
          const raw = localStorage.getItem("lumina.learningPath");
          return raw ? JSON.parse(raw) : null;
        } catch {
          return null;
        }
      },
      setLearningPath(pathData) {
        try {
          localStorage.setItem("lumina.learningPath", JSON.stringify(pathData));
        } catch (e) {
          console.error("Failed to save learning path in localStorage", e);
        }
      }
    },

    auth: {
      async register(payload) {
        const res = await request("/auth/register/", {
          method: "POST",
          body: payload
        });
        if (res.status === "success" && res.user) {
          API.storage.setUser(res.user);
        }
        return res;
      },

      async login(payload) {
        const res = await request("/auth/login/", {
          method: "POST",
          body: payload
        });
        if (res.status === "success" && res.user) {
          API.storage.setUser(res.user);
        }
        return res;
      },

      async me() {
        try {
          const res = await request("/auth/me/", { method: "GET" });
          if (res.status === "success" && res.user) {
            API.storage.setUser(res.user);
            return res.user;
          }
        } catch (err) {
          API.storage.clearUser();
          return null;
        }
        return null;
      },

      async logout() {
        try {
          await request("/auth/logout/", { method: "POST" });
        } finally {
          API.storage.clearUser();
        }
      }
    },

    learning: {
      async onboarding(payload) {
        return request("/onboarding/", {
          method: "POST",
          body: payload
        });
      },

      async createMaterial(payload) {
        let options = { method: "POST" };
        if (payload instanceof FormData) {
          options.body = payload;
        } else {
          options.body = payload;
        }
        return request("/material/create/", options);
      },

      async generatePath(payload) {
        return request("/path/generate/", {
          method: "POST",
          body: payload
        });
      async getStepQuiz(stepId) {
        return request(`/step/${stepId}/quiz/`, {
          method: "GET"
        });
      },

      async submitCheckpoint(payload) {
        return request("/checkpoint/submit/", {
          method: "POST",
          body: payload
        });
      },

      async getHint(questionId, level) {
        return request(`/hint/${questionId}/${level}/`, {
          method: "GET"
        });
      },

      async createChatThread(payload) {
        return request("/chat/thread/", {
          method: "POST",
          body: payload
        });
      },

      async chat(payload) {
        return request("/chat/", {
          method: "POST",
          body: payload
        });
      }
    }
  };

  window.API = API;
})(window);

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

  function showAILimitNotificationModal(msg) {
    if (document.getElementById("ai-limit-modal")) return;
    const standardKey = "AI System (OpenRouter) has reached the API rate limit or ran out of token quota. Please wait a few minutes and try again.";
    const modalHtml = `
      <div id="ai-limit-modal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
        <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl max-w-md w-full shadow-2xl border border-rose-500/30 space-y-4 text-center animate-fade-in-up">
          <div class="w-16 h-16 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center mx-auto text-3xl">
            <span class="material-symbols-outlined" style="font-size: 36px;">warning</span>
          </div>
          <h2 class="text-xl font-bold text-zinc-900 dark:text-zinc-100">AI API Limit Reached</h2>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">${escapeHtml(standardKey)}</p>
          <div class="flex flex-col gap-2 pt-2">
            <button id="close-ai-limit-modal-btn" class="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold text-xs shadow-md transition-all">
              <span>Got it</span>
            </button>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML("beforeend", modalHtml);
    window.LuminaNav?.translatePage?.();
    const closeBtn = document.getElementById("close-ai-limit-modal-btn");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        const el = document.getElementById("ai-limit-modal");
        if (el) el.remove();
      });
    }
  }

  function showDeleteCourseConfirmModal(courseTitle, onConfirm) {
    const existing = document.getElementById("delete-course-confirm-modal");
    if (existing) existing.remove();

    const titleText = courseTitle ? escapeHtml(courseTitle) : "This Course";
    const modalHtml = `
      <div id="delete-course-confirm-modal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
        <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl max-w-md w-full shadow-2xl border border-indigo-500/20 space-y-4 text-center animate-fade-in-up">
          <div class="w-14 h-14 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center mx-auto text-2xl">
            <span class="material-symbols-outlined" style="font-size: 32px;">delete</span>
          </div>
          <h2 class="text-lg font-bold text-zinc-900 dark:text-zinc-100">Are you sure you want to delete this course?</h2>
          <div class="bg-indigo-50 dark:bg-indigo-950/40 p-3 rounded-xl border border-indigo-500/20 font-bold text-xs text-indigo-700 dark:text-indigo-300 truncate max-w-full">
            📖 ${titleText}
          </div>
          <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">
            This action will remove all learning progress and AI materials. This cannot be undone.
          </p>
          <div class="flex items-center justify-end gap-3 pt-3 border-t border-zinc-200 dark:border-zinc-800">
            <button id="cancel-delete-course-btn" type="button" class="px-4 py-2.5 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 font-bold text-xs rounded-xl transition-all border border-zinc-300 dark:border-zinc-700">
              Cancel
            </button>
            <button id="confirm-delete-course-btn" type="button" class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 hover:opacity-80 text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center gap-1.5">
              <span class="material-symbols-outlined text-sm">delete</span>
              <span>Confirm Delete</span>
            </button>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML("beforeend", modalHtml);
    window.LuminaNav?.translatePage?.();

    const modal = document.getElementById("delete-course-confirm-modal");
    const cancelBtn = document.getElementById("cancel-delete-course-btn");
    const confirmBtn = document.getElementById("confirm-delete-course-btn");

    if (cancelBtn) {
      cancelBtn.addEventListener("click", () => {
        if (modal) modal.remove();
      });
    }

    if (confirmBtn) {
      confirmBtn.addEventListener("click", () => {
        if (modal) modal.remove();
        if (typeof onConfirm === "function") {
          onConfirm();
        } else {
          alert("Tính năng xóa khóa học đã được tiếp nhận và sẽ sớm đồng bộ dữ liệu.");
        }
      });
    }
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
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

        if (response.status === 401) {
          API.storage.clearUser();
          const page = window.location.pathname.split("/").pop().toLowerCase();
          if (page && page !== "lumina_learning_login_screen.html" && page !== "lumina_learning_landing_page.html") {
            window.location.href = "lumina_learning_login_screen.html";
          }
        }

        const isLimit = response.status === 429 || data.error_code === "AI_LIMIT_REACHED" ||
                        /giới hạn|quota|token|Rate Limit|429|402/i.test(errorMsg);
        if (isLimit) {
          showAILimitNotificationModal(errorMsg);
        }
        const error = new Error(errorMsg);
        error.status = response.status;
        error.data = data;
        error.isAILimit = isLimit;
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
          const matId = materialData.id || materialData.material_id;
          if (matId) {
            localStorage.setItem("lumina.lastMaterialId", matId);
          }
        } catch (e) {
          console.error("Failed to save material in localStorage", e);
        }
      },
      getLastMaterialId() {
        try {
          return localStorage.getItem("lumina.lastMaterialId");
        } catch {
          return null;
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
        } catch (e) {
          console.warn("Logout API warning:", e);
        } finally {
          API.storage.clearUser();
          API.storage.clearMaterial();
          const page = window.location.pathname.split("/").pop().toLowerCase();
          if (page !== "lumina_learning_login_screen.html" && page !== "lumina_learning_landing_page.html") {
            window.location.href = "lumina_learning_login_screen.html";
          }
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

      async getMaterials() {
        return request("/materials/", {
          method: "GET"
        });
      },

      async getCourses() {
        return request("/courses/", {
          method: "GET"
        });
      },

      async getMaterialDetail(materialId) {
        return request(`/material/${materialId}/`, {
          method: "GET"
        });
      },

      async deleteMaterial(materialId) {
        return request(`/material/${materialId}/delete/`, {
          method: "DELETE"
        });
      },

      async generatePath(payload) {
        return request("/path/generate/", {
          method: "POST",
          body: payload
        });
      },
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

      async getChatThread(scope, scopeId) {
        return request(`/chat/thread/?scope=${encodeURIComponent(scope)}&scope_id=${encodeURIComponent(scopeId)}`, {
          method: "GET"
        });
      },

      async getChatThreads() {
        return request("/chat/threads/", {
          method: "GET"
        });
      },

      async getChatThreadDetail(threadId) {
        return request(`/chat/thread/${threadId}/`, {
          method: "GET"
        });
      },

      async createNewChatThread(payload) {
        return request("/chat/thread/new/", {
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
    },
    showAILimitModal: showAILimitNotificationModal,
    showDeleteConfirmModal: showDeleteCourseConfirmModal
  };

  window.API = API;
})(window);

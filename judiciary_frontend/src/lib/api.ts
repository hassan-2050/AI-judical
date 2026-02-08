import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000/api";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Attach auth token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 401 globally
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      // Don't redirect if already on login page
      if (!window.location.pathname.includes("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

/* ---- Auth ---- */
export const authAPI = {
  register: (data: Record<string, unknown>) => api.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),
  getProfile: () => api.get("/auth/me"),
  updateProfile: (data: Record<string, unknown>) => api.put("/auth/me", data),
};

/* ---- Cases ---- */
export const casesAPI = {
  list: (params: Record<string, unknown>) => api.get("/cases", { params }),
  get: (id: string) => api.get(`/cases/${id}`),
  create: (data: Record<string, unknown>) => api.post("/cases", data),
  update: (id: string, data: Record<string, unknown>) =>
    api.put(`/cases/${id}`, data),
  delete: (id: string) => api.delete(`/cases/${id}`),
  stats: () => api.get("/cases/stats"),
};

/* ---- Search ---- */
export const searchAPI = {
  search: (params: Record<string, unknown>) => api.get("/search", { params }),
  filters: () => api.get("/search/filters"),
  suggest: (q: string) => api.get("/search/suggest", { params: { q } }),
};

/* ---- Scraper ---- */
export const scraperAPI = {
  run: (data: Record<string, unknown>) => api.post("/scraper/run", data),
  status: () => api.get("/scraper/status"),
  jobs: (params?: Record<string, unknown>) =>
    api.get("/scraper/jobs", { params }),
  job: (id: string) => api.get(`/scraper/jobs/${id}`),
  available: () => api.get("/scraper/available"),
};

/* ---- Analytics ---- */
export const analyticsAPI = {
  dashboard: () => api.get("/analytics/dashboard"),
  timeline: (year?: number) =>
    api.get("/analytics/timeline", { params: { year } }),
  courts: () => api.get("/analytics/courts"),
  judges: (limit?: number) =>
    api.get("/analytics/judges", { params: { limit } }),
};

/* ---- AI / Munsif AI ---- */
export const aiAPI = {
  chat: (data: { message: string; session_id?: string; language?: string }) =>
    api.post("/ai/chat", data),
  sessions: () => api.get("/ai/sessions"),
  getSession: (id: string) => api.get(`/ai/sessions/${id}`),
  deleteSession: (id: string) => api.delete(`/ai/sessions/${id}`),
  analyze: (caseId: string) => api.get(`/ai/analyze/${caseId}`),
  summarize: (caseId: string, sentences?: number) =>
    api.get(`/ai/summarize/${caseId}`, { params: { sentences } }),
  extract: (caseId: string) => api.get(`/ai/extract/${caseId}`),
  similar: (caseId: string, params?: { limit?: number; method?: string }) =>
    api.get(`/ai/similar/${caseId}`, { params }),
  extractText: (text: string) => api.post("/ai/extract-text", { text }),
};

/* ---- Documents ---- */
export const documentsAPI = {
  upload: (formData: FormData) =>
    api.post("/documents/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  list: (params?: Record<string, unknown>) =>
    api.get("/documents", { params }),
  get: (id: string) => api.get(`/documents/${id}`),
  delete: (id: string) => api.delete(`/documents/${id}`),
  process: (id: string) => api.post(`/documents/${id}/process`),
  download: (id: string) => api.get(`/documents/${id}/download`, { responseType: "blob" }),
};

/* ---- Translation ---- */
export const translationAPI = {
  translate: (data: { text: string; source_lang?: string; target_lang?: string }) =>
    api.post("/translate", data),
  glossary: (language?: string) =>
    api.get("/translate/glossary", { params: { language } }),
  detect: (text: string) => api.post("/translate/detect", { text }),
};

/* ---- Templates ---- */
export const templatesAPI = {
  list: (params?: Record<string, unknown>) =>
    api.get("/templates", { params }),
  get: (id: string) => api.get(`/templates/${id}`),
  create: (data: Record<string, unknown>) => api.post("/templates", data),
  generate: (id: string, values: Record<string, string>) =>
    api.post(`/templates/${id}/generate`, { values }),
  categories: () => api.get("/templates/categories"),
};

/* ---- Lawyers ---- */
export const lawyersAPI = {
  list: (params?: Record<string, unknown>) =>
    api.get("/lawyers", { params }),
  get: (id: string) => api.get(`/lawyers/${id}`),
  review: (id: string, data: { rating: number; comment?: string }) =>
    api.post(`/lawyers/${id}/review`, data),
  specializations: () => api.get("/lawyers/specializations"),
  cities: () => api.get("/lawyers/cities"),
};

/* ---- Notifications ---- */
export const notificationsAPI = {
  list: (params?: Record<string, unknown>) =>
    api.get("/notifications", { params }),
  create: (data: Record<string, unknown>) => api.post("/notifications", data),
  markRead: (id: string) => api.put(`/notifications/${id}/read`),
  markAllRead: () => api.put("/notifications/read-all"),
  delete: (id: string) => api.delete(`/notifications/${id}`),
  upcoming: (days?: number) =>
    api.get("/notifications/upcoming", { params: { days } }),
};

export default api;

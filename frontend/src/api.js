import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
export const API = `${BACKEND_URL}/api`;

const client = axios.create({ baseURL: API });

export const api = {
  getProfile: () => client.get("/profile").then((r) => r.data),
  updateProfile: (data) => client.put("/profile", data).then((r) => r.data),
  getTracks: () => client.get("/tracks").then((r) => r.data),
  discover: (data) => client.post("/discover", data).then((r) => r.data),
  getProfessors: () => client.get("/professors").then((r) => r.data),
  getBrief: (id) => client.post(`/professors/${id}/brief`).then((r) => r.data),
  generateDoc: (id, docType) => client.post(`/professors/${id}/generate/${docType}`).then((r) => r.data),
  updateRank: (id, rank) => client.patch(`/professors/${id}/rank`, { rank }).then((r) => r.data),
  downloadUrl: (id, docType) => `${API}/professors/${id}/download/${docType}`,
  pending: () => client.get("/outreach/pending").then((r) => r.data),
  history: () => client.get("/outreach/history").then((r) => r.data),
  markSent: (id) => client.post(`/outreach/${id}/send`).then((r) => r.data),
  skip: (id) => client.post(`/outreach/${id}/skip`).then((r) => r.data),
  updateOutreach: (id, data) => client.patch(`/outreach/${id}`, data).then((r) => r.data),
  addManual: (data) => client.post("/outreach/manual", data).then((r) => r.data),
  stats: () => client.get("/stats").then((r) => r.data),
};

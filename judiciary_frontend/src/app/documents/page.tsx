"use client";

import { useState, useEffect } from "react";
import { documentsAPI } from "@/lib/api";
import Loading from "@/components/common/Loading";
import type { LegalDocument, Pagination } from "@/types";
import {
  FiUpload,
  FiFile,
  FiTrash2,
  FiEye,
  FiDownload,
  FiCpu,
  FiCheckCircle,
  FiAlertTriangle,
  FiClock,
  FiX,
} from "react-icons/fi";
import toast from "react-hot-toast";

const DOC_TYPES = [
  { value: "judgment", label: "Judgment" },
  { value: "petition", label: "Petition" },
  { value: "affidavit", label: "Affidavit" },
  { value: "evidence", label: "Evidence" },
  { value: "contract", label: "Contract" },
  { value: "legal_notice", label: "Legal Notice" },
  { value: "power_of_attorney", label: "Power of Attorney" },
  { value: "other", label: "Other" },
];

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<LegalDocument[]>([]);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<LegalDocument | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    loadDocuments();
  }, [page]);

  async function loadDocuments() {
    try {
      const res = await documentsAPI.list({ page, page_size: 12 });
      setDocuments(res.data.documents || []);
      setPagination(res.data.pagination);
    } catch {
      toast.error("Failed to load documents. Please login first.");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const formData = new FormData(form);

    if (!formData.get("file")) {
      toast.error("Please select a file");
      return;
    }

    setUploading(true);
    try {
      await documentsAPI.upload(formData);
      toast.success("Document uploaded successfully!");
      setShowUpload(false);
      form.reset();
      loadDocuments();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } } };
      toast.error(error.response?.data?.error || "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleProcess(id: string) {
    try {
      await documentsAPI.process(id);
      toast.success("Document processed!");
      loadDocuments();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } } };
      toast.error(error.response?.data?.error || "Processing failed");
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this document?")) return;
    try {
      await documentsAPI.delete(id);
      toast.success("Document deleted");
      loadDocuments();
      if (selectedDoc?.id === id) setSelectedDoc(null);
    } catch {
      toast.error("Delete failed");
    }
  }

  async function viewDocument(id: string) {
    try {
      const res = await documentsAPI.get(id);
      setSelectedDoc(res.data.document);
    } catch {
      toast.error("Failed to load document details");
    }
  }

  function statusIcon(status: string) {
    switch (status) {
      case "processed":
        return <FiCheckCircle className="text-green-600" size={14} />;
      case "processing":
        return <FiClock className="text-yellow-600 animate-spin" size={14} />;
      case "failed":
        return <FiAlertTriangle className="text-red-600" size={14} />;
      default:
        return <FiClock className="text-gray-400" size={14} />;
    }
  }

  if (loading) return <Loading text="Loading documents..." />;

  return (
    <div className="page-container">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="page-title mb-0">Document Management</h1>
          <p className="text-gray-500 text-sm">
            Upload, process, and manage legal documents with AI-powered extraction
          </p>
        </div>
        <button onClick={() => setShowUpload(true)} className="btn-primary flex items-center gap-2">
          <FiUpload size={16} /> Upload Document
        </button>
      </div>

      {/* Upload Modal */}
      {showUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Upload Document</h2>
              <button onClick={() => setShowUpload(false)}><FiX size={20} /></button>
            </div>
            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">File</label>
                <input
                  type="file"
                  name="file"
                  accept=".pdf,.txt,.doc,.docx,.png,.jpg,.jpeg"
                  className="input"
                  required
                />
                <p className="text-xs text-gray-400 mt-1">Max 10MB. Supported: PDF, TXT, DOC, DOCX, Images</p>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Document Type</label>
                <select name="doc_type" className="input">
                  {DOC_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-3 justify-end">
                <button type="button" onClick={() => setShowUpload(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" disabled={uploading} className="btn-primary">
                  {uploading ? "Uploading..." : "Upload"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Document Grid */}
      {documents.length === 0 ? (
        <div className="text-center py-20">
          <FiFile className="mx-auto text-gray-300 mb-4" size={48} />
          <p className="text-gray-500 text-lg mb-2">No documents yet</p>
          <p className="text-gray-400 text-sm mb-6">Upload your first legal document to get started</p>
          <button onClick={() => setShowUpload(true)} className="btn-primary">
            <FiUpload size={16} className="inline mr-2" /> Upload Document
          </button>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {documents.map((doc) => (
            <div key={doc.id} className="card hover:shadow-md transition">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <FiFile className="text-primary-600 flex-shrink-0" size={20} />
                  <div className="min-w-0">
                    <p className="font-medium text-sm truncate">{doc.original_filename}</p>
                    <p className="text-xs text-gray-400">
                      {(doc.file_size / 1024).toFixed(1)} KB • {doc.doc_type.replace(/_/g, " ")}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {statusIcon(doc.status)}
                  <span className="text-xs capitalize text-gray-500">{doc.status}</span>
                </div>
              </div>

              {doc.summary && (
                <p className="text-xs text-gray-600 mb-3 line-clamp-2">{doc.summary}</p>
              )}

              {doc.entities.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {doc.entities.slice(0, 4).map((e, i) => (
                    <span key={i} className="badge bg-blue-50 text-blue-700 text-[10px]">
                      {e.entity_type}: {e.value.slice(0, 20)}
                    </span>
                  ))}
                  {doc.entities.length > 4 && (
                    <span className="badge bg-gray-50 text-gray-500 text-[10px]">
                      +{doc.entities.length - 4} more
                    </span>
                  )}
                </div>
              )}

              <div className="flex gap-2 pt-3 border-t">
                <button onClick={() => viewDocument(doc.id)} className="text-xs btn-secondary flex-1 flex items-center justify-center gap-1">
                  <FiEye size={12} /> View
                </button>
                {doc.status === "uploaded" && (
                  <button onClick={() => handleProcess(doc.id)} className="text-xs btn-primary flex-1 flex items-center justify-center gap-1">
                    <FiCpu size={12} /> Process
                  </button>
                )}
                <button onClick={() => handleDelete(doc.id)} className="text-xs btn-danger px-3">
                  <FiTrash2 size={12} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {pagination && pagination.total_pages > 1 && (
        <div className="flex justify-center gap-2 mt-6">
          {Array.from({ length: pagination.total_pages }, (_, i) => i + 1).map((p) => (
            <button
              key={p}
              onClick={() => setPage(p)}
              className={`px-3 py-1 rounded ${
                p === page ? "bg-primary-600 text-white" : "bg-white border hover:bg-gray-50"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Document Detail Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[80vh] overflow-y-auto m-4 p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-lg font-semibold">{selectedDoc.original_filename}</h2>
                <p className="text-sm text-gray-500">
                  {selectedDoc.doc_type.replace(/_/g, " ")} •{" "}
                  {(selectedDoc.file_size / 1024).toFixed(1)} KB •
                  Status: {selectedDoc.status}
                </p>
              </div>
              <button onClick={() => setSelectedDoc(null)}><FiX size={20} /></button>
            </div>

            {selectedDoc.summary && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-1">AI Summary</h3>
                <p className="text-sm text-gray-600 bg-blue-50 p-3 rounded-lg">{selectedDoc.summary}</p>
              </div>
            )}

            {selectedDoc.entities.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-semibold mb-2">Extracted Entities</h3>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(
                    selectedDoc.entities.reduce((acc: Record<string, string[]>, e) => {
                      (acc[e.entity_type] = acc[e.entity_type] || []).push(e.value);
                      return acc;
                    }, {})
                  ).map(([type, values]) => (
                    <div key={type} className="bg-gray-50 p-2 rounded">
                      <p className="text-xs font-semibold text-gray-500 mb-1">{type}</p>
                      {(values as string[]).map((v, i) => (
                        <p key={i} className="text-xs text-gray-700">{v}</p>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selectedDoc.extracted_text && (
              <div>
                <h3 className="text-sm font-semibold mb-1">Extracted Text</h3>
                <div className="bg-gray-50 p-3 rounded-lg max-h-60 overflow-y-auto">
                  <pre className="text-xs whitespace-pre-wrap font-mono">{selectedDoc.extracted_text}</pre>
                </div>
              </div>
            )}

            <div className="flex gap-3 mt-4 pt-4 border-t">
              <button onClick={() => handleProcess(selectedDoc.id)} className="btn-primary text-sm flex items-center gap-1">
                <FiCpu size={14} /> Re-process
              </button>
              <button onClick={() => setSelectedDoc(null)} className="btn-secondary text-sm">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

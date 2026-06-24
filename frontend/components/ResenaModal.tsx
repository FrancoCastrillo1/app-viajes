"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

interface ResenaModalProps {
  viajeId: number;
  receptorId: number;
  receptorNombre: string;
  onClose: () => void;
}

export default function ResenaModal({ viajeId, receptorId, receptorNombre, onClose }: ResenaModalProps) {
  const [estrellas, setEstrellas] = useState(0);
  const [comentario, setComentario] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (estrellas < 1 || estrellas > 5) {
      toast.error("Seleccioná una calificación.");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/api/resenas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ viajeId, receptorId, estrellas, comentario }),
      });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message || "¡Reseña enviada!");
        onClose();
        router.refresh();
      } else {
        toast.error(data.error || "No se pudo enviar la reseña.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>✕</button>
        <h3 className="modal-title">Calificar a {receptorNombre}</h3>

        <form onSubmit={handleSubmit}>
          <div className="stars-input">
            {[5, 4, 3, 2, 1].map((n) => (
              <label key={n} style={{ color: n <= estrellas ? "#F59E0B" : "#E5E7EB", cursor: "pointer", fontSize: "2.2rem" }}
                onClick={() => setEstrellas(n)}>
                ★
              </label>
            ))}
          </div>

          <textarea
            className="resena-textarea"
            placeholder="Contá tu experiencia (opcional)..."
            value={comentario}
            onChange={(e) => setComentario(e.target.value.slice(0, 500))}
            maxLength={500}
          />
          <div className="resena-char-counter">{comentario.length}/500</div>

          <button type="submit" className="btn-auth" disabled={loading}>
            {loading ? "Enviando..." : "Enviar reseña"}
          </button>
        </form>
      </div>
    </div>
  );
}

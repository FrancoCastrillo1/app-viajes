import Link from "next/link";
import Image from "next/image";
import { CITIES } from "@/lib/cities";
import SearchForm from "@/components/SearchForm";

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="hero-inner">
          <div className="hero-badge">🚗 Viajes compartidos en Argentina</div>
          <h1 className="hero-title">
            Viajá junto a otros.<br />
            <span className="hero-highlight">Lleguen más lejos.</span>
          </h1>
          <p className="hero-sub">
            Encontrá personas que hacen tu misma ruta y compartí los gastos. Más barato, más social, más sustentable.
          </p>
          <div className="hero-ctas">
            <Link href="/viajes" className="hero-btn-primary">Ver viajes disponibles</Link>
            <Link href="/register" className="hero-btn-secondary">Publicar mi viaje →</Link>
          </div>
        </div>
        <div className="hero-img-wrap">
          <Image src="/img/hero-bg.png" alt="Viajeros cargando el baúl" className="hero-photo" fill style={{ objectFit: "cover" }} priority />
        </div>
      </section>

      <div className="search-wrapper">
        <div className="search-card">
          <h2 className="search-heading">📍 ¿A dónde vas hoy?</h2>
          <SearchForm cities={CITIES} />
          <Link href="/viajes" className="link-all-trips">Ver todos los viajes disponibles →</Link>
        </div>
      </div>

      <section className="features-section">
        <div className="features-inner">
          {[
            { emoji: "🛡️", title: "Conductores verificados", desc: "Cada conductor confirma su identidad antes de publicar un viaje." },
            { emoji: "💬", title: "Contacto directo", desc: "Coordiná con el conductor por WhatsApp sin intermediarios." },
            { emoji: "💸", title: "Ahorrá hasta 50%", desc: "Compartí los gastos y llegá a destino por mucho menos." },
            { emoji: "🌿", title: "Viajá sustentable", desc: "Menos autos en la ruta, menos emisiones, más planeta." },
          ].map((f) => (
            <div key={f.title} className="feature-card">
              <div className="feature-emoji">{f.emoji}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="social-section">
        <div className="social-inner">
          <div className="social-text">
            <span className="social-tag">Una comunidad real</span>
            <h2 className="social-title">Más que un viaje,<br />una <em>conexión</em></h2>
            <p className="social-desc">En Ruta Compartida viajás con personas reales de tu zona. Hacés el camino más corto, más divertido y más económico.</p>
          </div>
          <div className="social-img-wrap">
            <Image src="/img/foto-juntos.png" alt="Amigos viajando juntos" className="social-photo" width={500} height={380} style={{ objectFit: "cover", borderRadius: "var(--radius-xl)" }} />
            <div className="social-img-badge">¡Viajando en Ruta Compartida! 🗺️</div>
          </div>
        </div>
      </section>

      <section className="how-section">
        <h2 className="how-title">¿Cómo funciona?</h2>
        <p className="how-sub">En tres pasos simples ya estás viajando</p>
        <div className="how-steps">
          <div className="step">
            <div className="step-num">01</div>
            <div className="step-text"><h4>Buscá tu ruta</h4><p>Ingresá origen, destino y fecha para ver los viajes disponibles.</p></div>
          </div>
          <div className="step-divider">· · ·</div>
          <div className="step">
            <div className="step-num">02</div>
            <div className="step-text"><h4>Reservá tu lugar</h4><p>Confirmá tu asiento con un solo clic. Te llega confirmación por mail.</p></div>
          </div>
          <div className="step-divider">· · ·</div>
          <div className="step">
            <div className="step-num">03</div>
            <div className="step-text"><h4>Coordiná y viajá</h4><p>Hablá con el conductor por WhatsApp y acordá el punto de encuentro.</p></div>
          </div>
        </div>
      </section>

      <section className="trust-section">
        <div className="trust-inner">
          <div className="trust-img-wrap">
            <Image src="/img/foto-saludo.png" alt="Conductor y pasajero" className="trust-photo" width={500} height={380} style={{ objectFit: "cover", borderRadius: "var(--radius-xl)" }} />
          </div>
          <div className="trust-text">
            <span className="social-tag">Seguridad primero</span>
            <h2 className="social-title">Viajás con alguien<br />en quien podés <em>confiar</em></h2>
            <p className="social-desc">Verificamos la identidad de cada conductor antes de que publique. Podés cancelar cuando necesitás.</p>
            <ul className="trust-list">
              <li>✅ Identidad verificada por mail</li>
              <li>✅ Contacto directo vía WhatsApp</li>
              <li>✅ Cancelación sin costo</li>
              <li>✅ Notificaciones en tiempo real</li>
            </ul>
            <Link href="/register" className="trust-cta">Crear mi cuenta gratis →</Link>
          </div>
        </div>
      </section>
    </>
  );
}

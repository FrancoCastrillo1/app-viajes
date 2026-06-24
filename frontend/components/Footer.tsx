import Link from "next/link";

export default function Footer() {
  return (
    <>
      <section className="contact-section">
        <div className="contact-container">
          <h3>¿Tenés dudas?</h3>
          <p>
            Escribinos a{" "}
            <a href="mailto:rutacompartida.soporte@gmail.com">
              rutacompartida.soporte@gmail.com
            </a>
          </p>
        </div>
      </section>

      <footer className="main-footer">
        <div className="footer-grid">
          <div className="footer-col-brand">
            <Link href="/" className="footer-logo-link">Ruta Compartida</Link>
            <p className="footer-tagline">Viajá seguro, viajá acompañado.</p>
          </div>

          <div>
            <p className="footer-col-heading">Navegación</p>
            <div className="footer-col-links">
              <Link href="/viajes">Buscar Viajes</Link>
              <Link href="/crear-viaje">Publicar viaje</Link>
              <Link href="/terminos">Términos y Condiciones</Link>
            </div>
          </div>

          <div className="footer-col-contact">
            <p className="footer-col-heading">Contacto</p>
            <p>¿Preguntas o reportes?</p>
            <a href="mailto:rutacompartida.soporte@gmail.com">
              rutacompartida.soporte@gmail.com
            </a>
          </div>
        </div>

        <hr className="footer-divider" />

        <div className="footer-bottom">
          <p>&copy; 2026 Ruta Compartida. Todos los derechos reservados.</p>
        </div>
      </footer>
    </>
  );
}

import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Ruta Compartida",
    short_name: "RutaComp",
    description: "Viajes compartidos en Argentina",
    start_url: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#ffffff",
    theme_color: "#E76F51",
    icons: [
      { src: "/img/logo.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/img/logo.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}

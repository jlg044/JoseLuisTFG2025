// utils.js
const zonas = [
  { nombre: 'Entrada', xMin: 0, xMax: 2.65, yMin: 4.5, yMax: 6.8 },
  { nombre: 'Ordenador', xMin: 2.65, xMax: 4.85, yMin: 3.55, yMax: 6.8 },
  { nombre: 'Salón', xMin: 4.85, xMax: 8.38, yMin: 3.55, yMax: 6.8 },
  { nombre: 'Cocina', xMin: 0, xMax: 2.65, yMin: 0, yMax: 4.5 },
  { nombre: 'Baño', xMin: 2.65, xMax: 5.18, yMin: 0, yMax: 3.55 },
  { nombre: 'Habitación', xMin: 5.18, xMax: 8.38, yMin: 0, yMax: 3.55 },
];

function obtenerFechaYFase() {
  const ahora = new Date();
  const fecha = ahora.toISOString().slice(0, 10);
  const hora = ahora.getHours();
  const fase = hora < 12 ? 'mañana' : 'tarde';
  return { fecha, fase };
}

function obtenerZona(x, y) {
  const zona = zonas.find(z =>
    x >= z.xMin && x <= z.xMax &&
    y >= z.yMin && y <= z.yMax
  );
  return zona ? zona.nombre : 'Desconocida';
}

module.exports = {
  obtenerFechaYFase,
  obtenerZona,
  zonas
};

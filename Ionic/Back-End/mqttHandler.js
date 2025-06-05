const mqtt = require('mqtt');
const { Posicion, ZonaVisitada } = require('./models/posicion');
const { obtenerFechaYFase, obtenerZona, zonas } = require('./utils');

function initMQTT(broker, topic) {
  const client = mqtt.connect(broker);

  client.on('connect', () => {
    console.log(`Conectado a ${broker}`);
    client.subscribe(topic);
  });

  client.on('message', async (topic, message) => {
    try {
      const { x, y, dispositivo, timestamp } = JSON.parse(message.toString());
      const { fecha, fase } = obtenerFechaYFase();
      const zona = obtenerZona(x, y);

      // Guardar en "posicions"
      const nueva = new Posicion({ x, y, dispositivo, timestamp, fecha, fase });
      await nueva.save();

      // Guardar en "zonasvisitadas"
      const resumen = new ZonaVisitada({ x, y, dispositivo, timestamp, fecha, fase, zona });
      await resumen.save();

      console.log(`Guardado en ambas colecciones: ${dispositivo} en zona ${zona}`);
    } catch (err) {
      console.error('Error procesando mensaje MQTT:', err);
    }
  });
}

module.exports = { initMQTT };

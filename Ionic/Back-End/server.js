require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const { initMQTT } = require('./mqttHandler');
const { obtenerFechaYFase, obtenerZona, zonas } = require('./utils');

const app = express();
app.use(cors());
app.use(express.json());

// Conexión a MongoDB
mongoose.connect(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true
}).then(() => {
  console.log('Conectado a MongoDB');
}).catch(err => {
  console.error('Error al conectar a MongoDB:', err);
});

// Inicializar MQTT
initMQTT(process.env.MQTT_BROKER, process.env.MQTT_TOPIC);

// Iniciar servidor
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
});

// WebSocket en puerto 4000
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 4000 });

function broadcast(data) {
  const json = JSON.stringify(data);
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(json);
    }
  });
}

const { Posicion, ZonaVisitada } = require('./models/posicion');

// Obtener la última posición de un dispositivo
app.get('/api/posicion/:dispositivo', async (req, res) => {
  const dispositivo = req.params.dispositivo;

  try {
    const ultima = await Posicion.findOne({ dispositivo }).sort({ timestamp: -1 });
    if (ultima) {
      res.json(ultima);
    } else {
      res.status(404).json({ error: 'No hay posiciones para ese dispositivo' });
    }
  } catch (error) {
    res.status(500).json({ error: 'Error interno del servidor' });
  }
});

// Obtener los contadores de zona por fecha y fase
app.get('/api/zonas/:dispositivo/:fecha/:fase', async (req, res) => {
  const { dispositivo, fecha, fase } = req.params;

  try {
    const visitas = await ZonaVisitada.find({ dispositivo, fecha, fase });

    const zonasContadas = zonas.map(z => ({ ...z, contador: 0 }));

    for (const v of visitas) {
      const zona = zonasContadas.find(z => z.nombre === v.zona);
      if (zona) zona.contador++;
    }

    res.json(zonasContadas);
  } catch (err) {
    res.status(500).json({ error: 'Error al obtener zonas' });
  }
});

// Guardar nueva posición y enviar por WS
app.post('/api/posicion', async (req, res) => {
  const { x, y, dispositivo, timestamp } = req.body;

  if (x === undefined || y === undefined || !dispositivo || !timestamp) {
    return res.status(400).json({ error: 'Faltan datos en el cuerpo de la petición' });
  }

  const { fecha, fase } = obtenerFechaYFase();
  const zona = obtenerZona(x, y);

  try {
    const nueva = new Posicion({ x, y, dispositivo, timestamp, fecha, fase });
    await nueva.save();

    const resumen = new ZonaVisitada({ x, y, dispositivo, timestamp, fecha, fase, zona });
    await resumen.save();

    broadcast({ x, y, zona, dispositivo, fase });

    res.status(200).json({ mensaje: 'Guardado correctamente' });
  } catch (error) {
    console.error('Error al guardar en MongoDB:', error);
    res.status(500).json({ error: 'Error interno del servidor' });
  }
});

app.get('/api/ultimo-dispositivo', async (req, res) => {
  try {
    const ultima = await Posicion.findOne().sort({ timestamp: -1 });
    if (ultima) {
      res.json({ dispositivo: ultima.dispositivo });
    } else {
      res.status(404).json({ error: 'No hay dispositivos registrados' });
    }
  } catch (err) {
    res.status(500).json({ error: 'Error al obtener último dispositivo' });
  }
});
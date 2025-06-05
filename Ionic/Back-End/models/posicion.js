const mongoose = require('mongoose');

const posicionSchema = new mongoose.Schema({
  timestamp: Number,
  dispositivo: String,
  x: Number,
  y: Number
});

const Posicion = mongoose.model('Posicion', posicionSchema);

const zonaVisitadaSchema = new mongoose.Schema({
  timestamp: Number,
  dispositivo: String,
  x: Number,
  y: Number,
  fecha: String,
  fase: String,
  zona: String
});

const ZonaVisitada = mongoose.model('ZonaVisitada', zonaVisitadaSchema);

module.exports = { Posicion, ZonaVisitada };


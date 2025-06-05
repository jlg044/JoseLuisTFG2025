import { Component, OnInit } from '@angular/core';
import mqtt from 'mqtt';
import { HttpClient } from '@angular/common/http';

interface Zona {
  nombre: string;
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
  tiempo: number;
  contador: number;
}

@Component({
  standalone: false,
  selector: 'app-home',
  templateUrl: './home.page.html',
  styleUrls: ['./home.page.scss'],
})
export class HomePage implements OnInit {
  posX = 50;
  posY = 50;
  mqttClient!: mqtt.MqttClient;
  coordenadasRecibidas = false;

  modoMapa = 'ubi';

  readonly MQTT_BROKER = 'ws://172.21.144.1:9001';
  readonly xMax = 8.38;
  readonly yMax = 6.8;

  zonas: Zona[] = [
    { nombre: 'Entrada', xMin: 0, xMax: 2.65, yMin: 4.5, yMax: 6.8, tiempo: 0, contador: 0 },
    { nombre: 'Ordenador', xMin: 2.65, xMax: 4.85, yMin: 3.55, yMax: 6.8, tiempo: 0, contador: 0 },
    { nombre: 'Salón', xMin: 4.85, xMax: 8.38, yMin: 3.55, yMax: 6.8, tiempo: 0, contador: 0 },
    { nombre: 'Cocina', xMin: 0, xMax: 2.65, yMin: 0, yMax: 4.5, tiempo: 0, contador: 0 },
    { nombre: 'Baño', xMin: 2.65, xMax: 5.18, yMin: 0, yMax: 3.55, tiempo: 0, contador: 0 },
    { nombre: 'Habitación', xMin: 5.18, xMax: 8.38, yMin: 0, yMax: 3.55, tiempo: 0, contador: 0 },
  ];

  zonaActual: string | null = null;
  zonaActualObj?: Zona;
  intervalo: any;
  ubicacionX = 0;
  ubicacionY = 0;

  nuevoDispositivo = '';
  faseVisualizada = 'mañana';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.recuperarDispositivo().then(() => {
      this.obtenerUltimaPosicion();
      this.connectMQTT();
      this.faseVisualizada = this.getFechaYFase().fase;
      this.actualizarContadoresPorFase();
      this.conectarWebSocket();

      this.intervalo = setInterval(() => {
        if (this.modoMapa === 'calor') {
          this.actualizarContadoresPorFase();
        }
      }, 10000);
    });
  }

  async recuperarDispositivo() {
    const guardado = localStorage.getItem('dispositivo');
    if (guardado) {
      this.nuevoDispositivo = guardado;
    } else {
      try {
        const data = await this.http.get<any>('http://localhost:3000/api/ultimo-dispositivo').toPromise();
        this.nuevoDispositivo = data?.dispositivo || '';
        localStorage.setItem('dispositivo', this.nuevoDispositivo);
      } catch (err) {
        console.warn('No se pudo recuperar el último dispositivo:', err);
      }
    }
  }

  obtenerUltimaPosicion() {
    if (!this.nuevoDispositivo) return;

    this.http.get<any>(`http://localhost:3000/api/posicion/${this.nuevoDispositivo}`)
      .subscribe({
        next: data => this.updateMarker(data.x, data.y),
        error: err => console.warn('Error al obtener última posición:', err)
      });
  }

  actualizarContadoresPorFase() {
    const { fecha } = this.getFechaYFase();
    const fase = this.faseVisualizada;
    this.http.get<any[]>(`http://localhost:3000/api/zonas/${this.nuevoDispositivo}/${fecha}/${fase}`)
      .subscribe({
        next: zonasServidor => {
          console.log('🔁 Datos de zonas (fase:', fase, '):', zonasServidor);
          this.zonas.forEach(z => {
            const zonaServ = zonasServidor.find(s => s.nombre === z.nombre);
            if (zonaServ) z.contador = zonaServ.contador;
          });
        },
        error: err => console.warn('Error al recuperar zonas de calor:', err)
      });
  }

  conectarWebSocket() {
    const socket = new WebSocket('ws://localhost:4000');

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const { x, y, zona, dispositivo, fase } = data;

      // Ignorar datos que no sean del mismo día/fase
      if (fase !== this.faseVisualizada) return;

      // Si llega otro dispositivo por WebSocket, lo actualizamos
      if (dispositivo !== this.nuevoDispositivo) {
        this.nuevoDispositivo = dispositivo;
        localStorage.setItem('dispositivo', dispositivo);
        this.actualizarContadoresPorFase();
      }

      this.updateMarker(x, y);
      const z = this.zonas.find(z => z.nombre === zona);
      if (z) {
        z.contador += 1;
        this.zonaActual = zona;
        this.zonaActualObj = z;
      }
    };

    socket.onerror = err => console.error('WebSocket error:', err);
  }

  connectMQTT() {
    this.mqttClient = mqtt.connect(this.MQTT_BROKER, {
      reconnectPeriod: 5000,
    });

    this.mqttClient.on('connect', () => console.log('MQTT conectado'));
    this.mqttClient.on('error', (err) => console.error('MQTT error:', err));
  }

  updateMarker(x: number, y: number) {
    const safeX = Math.min(Math.max(x, 0), this.xMax);
    const safeY = Math.min(Math.max(y, 0), this.yMax);
    this.ubicacionX = safeX;
    this.ubicacionY = safeY;
    this.coordenadasRecibidas = true;
    this.posX = (safeX / this.xMax) * 100;
    this.posY = (1 - (safeY / this.yMax)) * 100;
  }

  /* Tiempo
  obtenerColor(tiempo: number): string {
    if (tiempo > 720) return 'rgba(251, 60, 60, 0.6)';
    if (tiempo > 360) return 'rgb(252, 167, 167)';
    if (tiempo > 120)  return 'rgb(250, 206, 206)';
    return ' #cccccc88';
  }
  */

  obtenerColor(contador: number): string {
    const max = 100;
    const intensidad = Math.min(1, contador / max);
    const red = 255;
    const green = Math.floor(255 * (1 - intensidad));
    const blue = Math.floor(255 * (1 - intensidad));
    return `rgba(${red},${green},${blue},0.5)`;
  }

  cambiarModo(event: any) {
    if (this.modoMapa === 'calor') {
      this.faseVisualizada = this.getFechaYFase().fase;
      this.actualizarContadoresPorFase();
    }
  }

  ionViewWillLeave() {
    if (this.mqttClient) this.mqttClient.end();
    clearInterval(this.intervalo);
  }

  enviarNombreDispositivo() {
    if (this.nuevoDispositivo.trim()) {
      const mensaje = JSON.stringify({ device: this.nuevoDispositivo.trim() });
      this.mqttClient.publish('Ion/disp', mensaje);
      localStorage.setItem('dispositivo', this.nuevoDispositivo.trim());
    }
  }

  getFechaYFase(): { fecha: string; fase: string } {
    const ahora = new Date();
    const fecha = ahora.toISOString().slice(0, 10);
    const hora = ahora.getHours();
    const fase = hora < 12 ? 'mañana' : 'tarde';
    return { fecha, fase };
  }
}

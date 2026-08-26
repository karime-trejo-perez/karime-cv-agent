# Proyectos

## IoT Smart Home Energy Controller
**Fecha:** Junio 2026
**Stack:** Arduino UNO Q, Edge Impulse, Transfer Learning

Diseñó y construyó un sistema inteligente de gestión de energía basado en el Arduino
UNO Q (producto proporcionado por Qualcomm, con unidades dedicadas de procesamiento de IA y
voz), permitiendo visualización de consumo eléctrico en tiempo real por carga
y control remoto independiente de 4 canales de salida AC/DC. Entrenó un
modelo de reconocimiento de comandos de voz vía transfer learning en Edge
Impulse, usando extracción de características de audio basada en
espectrogramas, logrando 87% de precisión en 7 comandos distintos para
control de dispositivos manos libres.

## Voice-Controlled Access System with Deep Learning
**Fecha:** Marzo 2026
**Stack:** Python, VGG16, Deep Learning

Implementó un sistema de autenticación biométrica de dos factores en cascada,
integrando un módulo de Keyword Spotting (KWS) basado en VGG16 fine-tuneado y
un módulo de 'Speaker Verification' (SV) mediante un pipeline de Deep
Learning. Logró 96.92% de precisión en KWS y 2.56 falsas alarmas por hora
bajo pruebas de estrés fuera de distribución, manteniendo una latencia de
inferencia extremo a extremo de ~397 ms en hardware CPU.

## Autonomous Mapless Navigation via Deep Q-Learning
**Fecha:** Marzo 2026
**Stack:** Python, DQN (Deep Q-Learning)

Diseñó un sistema de navegación autónoma usando Deep Reinforcement Learning
(DQN) con un vector de estado multimodal de 17 dimensiones que integra
exterocepción, propiocepción y memoria espacial. Alcanzó 99.33% de tasa de
éxito y 0.855 de SPL sobre 10,000 episodios de auditoría, sin depender de
mapas topológicos globales.

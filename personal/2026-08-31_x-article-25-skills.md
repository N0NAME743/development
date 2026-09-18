# 【保存ログ】25 Skills de productividad para Claude, ChatGPT y Gemini

## メタデータ

| 項目 | 内容 |
|---|---|
| 記事タイトル | 25 Skills de productividad para Claude, ChatGPT y Gemini |
| 投稿者 | Nico (@nicos_ai) |
| 元URL | https://x.com/nicos_ai/status/2053870934965043354 |
| 投稿日 | 2026年5月12日 |
| 反響 | 返信16・リポスト183・いいね1,220・閲覧146万 |
| 保存元ファイル | `X.htm`（ブラウザで保存したページ、`X_files/`に画像同梱） |
| ログ作成日 | 2026-08-31 |

## 日本語サマリー

X（旧Twitter）のArticle機能で公開された長文記事。Claude Skills形式（`name:`/`description:`のフロントマター＋Markdown本文）で書かれた**プロダクティビティ向けプロンプトテンプレート25個**を無料公開している。著者いわくClaude以外でもコピペでChatGPT/Geminiに使い回せる。

5カテゴリの内訳:

| カテゴリ | 件数 | 内容 |
|---|---|---|
| 📚 学生向け (Estudiantes) | 7 | 構造化ノート生成・試験対策・学習ロードマップ・難解概念解説・論文ドラフト・フラッシュカード・学習計画 |
| 💼 業務生産性 (Productividad Laboral) | 4 | ビジネスメール・議事録整理・CV/LinkedIn最適化・プレゼン準備 |
| 🔍 リサーチ・分析 (Investigación y Análisis) | 4 | リサーチ要約・情報源検証・知識構造化・競合分析 |
| 🎬 動画・映像 (Vídeo y Contenido Visual) | 3 | 動画台本・フック生成・フローチャート |
| 💻 コード・自動化 (Código y Automatización) | 7 | コード文書化・ユニットテスト・デバッグ・正規表現・コミットメッセージ・コードレビュー・自動化エージェント |

**評価**: 無料API勧誘系の投稿とは異なり、アカウント登録や外部リンクを要求せず、中身（プロンプト全文）が記事内に直接公開されている実用的な内容。

---

## 元テキスト（記事本文・原文スペイン語、抽出）

> ブラウザ保存された `X.htm` から HTML タグを除去して抽出した本文。25個のスキル定義（`name:` / `description:` フロントマター＋Markdown本文）を含む。

```text
En este artículo he recopilado 25 skills que puedes añadir a cualquier modelo de IA para disparar tu productividad. Cada skill está escrita en formato .md, que es el estándar para Claude. Aun así, puedes copiar el contenido y pegarlo en ChatGPT o Gemini cuando necesites usar la skill. He organizado las skills en 5 categorías y también he incluido una guía en vídeo que muestra cómo añadir estas skills a tu agente de Claude fácilmente: 0:00 / 1:35 Guía de Instalación de Skills en Claude 📚 Estudiantes 1. Generador de Apuntes Estructurados Le metes un tema, un PDF de clase o la transcripción de un vídeo y te devuelve apuntes organizados con conceptos clave, definiciones, ejemplos y un esquema visual. Tipo Notion pero automático. name: structured-notes-generator
 description: Transforma temas, PDFs de clase o transcripciones en apuntes organizados con conceptos clave, definiciones, ejemplos, esquemas y preguntas de repaso.
---
# Generador de Apuntes Estructurados
## Resumen
Convierte cualquier fuente de contenido educativo en apuntes limpios, jerárquicos y listos para estudiar. Extrae lo esencial, lo organiza por bloques temáticos y añade elementos que facilitan la retención.
**Palabras clave**: apuntes, estudio, resumen, conceptos, definiciones, esquema, repaso
## Características
- Extracción de conceptos clave y definiciones
- Organización jerárquica por temas y subtemas
- Inclusión de ejemplos y analogías
- Sección de preguntas de repaso al final
- Esquema visual del tema (mapa de relaciones)
## Formato de Salida
- Título del tema
- Esquema general (índice)
- Bloques por subtema con: concepto → definición → ejemplo
- Conexiones entre conceptos
- Preguntas de repaso (3-5)
## Instrucciones
- Analizar el contenido fuente completo
- Identificar conceptos principales y secundarios
- Organizar en jerarquía lógica (de general a específico)
- Añadir un ejemplo práctico o analogía por cada concepto complejo
- Generar preguntas de repaso que cubran los puntos más importantes
- Si hay fórmulas o datos numéricos, destacarlos en bloque separado
## Restricciones
- No inventar información que no esté en la fuente
- No simplificar hasta perder precisión técnica
- Marcar con [AMPLIAR] conceptos que necesiten más contexto
- Mantener apuntes entre 500-1500 palabras salvo que el tema exija más 2. Preparador de Exámenes A partir de apuntes o temario, genera preguntas tipo test, de desarrollo y casos prácticos con respuestas. Básicamente un simulacro de examen personalizado. name: exam-prep-generator
 description: Genera exámenes de práctica a partir de apuntes o temario con preguntas tipo test, desarrollo y casos prácticos, incluyendo respuestas detalladas.
---
# Preparador de Exámenes
## Resumen
Crea simulacros de examen personalizados a partir del material que le proporciones. Genera preguntas de diferente tipo y dificultad para que practiques antes del examen real.
**Palabras clave**: examen, test, preguntas, estudio, repaso, simulacro, práctica
## Características
- Preguntas tipo test (4 opciones, una correcta)
- Preguntas de desarrollo corto
- Casos prácticos / problemas
- Respuestas detalladas con explicación
- Clasificación por dificultad (básico, intermedio, avanzado)
## Formato de Salida
- Bloque 1: Preguntas tipo test (5-10)
- Bloque 2: Preguntas de desarrollo (3-5)
- Bloque 3: Caso práctico (1-2)
- Sección de respuestas con explicación
## Instrucciones
- Analizar el material proporcionado
- Identificar los conceptos más evaluables
- Generar preguntas que cubran distintos niveles cognitivos (recordar, entender, aplicar, analizar)
- En el tipo test, incluir distractores realistas (no opciones absurdas)
- En desarrollo, pedir respuestas de 3-5 líneas
- En casos prácticos, plantear situaciones que requieran aplicar varios conceptos
- Incluir la respuesta correcta con explicación de por qué las otras son incorrectas
## Restricciones
- Basar todo en el material proporcionado
- No repetir el mismo concepto en varias preguntas
- Distribuir dificultad: 40% básico, 40% intermedio, 20% avanzado
- Marcar el nivel de cada pregunta 3. Generador de Roadmaps de Aprendizaje Le dices "quiero aprender X" y te monta un plan semana a semana con recursos, ejercicios y checkpoints para medir tu avance. name: learning-roadmap-generator
 description: Crea planes de aprendizaje estructurados semana a semana con objetivos, recursos recomendados, ejercicios prácticos y checkpoints de progreso.
---
# Generador de Roadmaps de Aprendizaje
## Resumen
Diseña rutas de aprendizaje personalizadas para cualquier tema. Desde "quiero aprender Python" hasta "necesito entender finanzas básicas". Genera un plan realista con hitos medibles.
**Palabras clave**: aprendizaje, roadmap, plan de estudio, recursos, objetivos, progreso
## Características
- Plan semanal con objetivos claros
- Recursos recomendados (gratuitos y de pago)
- Ejercicios prácticos por semana
- Checkpoints para evaluar progreso
- Adaptable al tiempo disponible del usuario
## Formato de Salida
- Objetivo final del roadmap
- Nivel actual asumido (o preguntar)
- Plan semana a semana:
 - Tema de la semana
 - Objetivo específico
 - Recursos (vídeos, artículos, cursos)
 - Ejercicio práctico
 - Checkpoint: "Sabrás que lo dominas cuando puedas..."
- Resumen del roadmap completo
## Instrucciones
- Preguntar o detectar el nivel actual del usuario
- Definir un objetivo final concreto y medible
- Dividir el camino en bloques semanales progresivos
- Cada semana debe construir sobre la anterior
- Incluir al menos un recurso gratuito por semana
- Los checkpoints deben ser verificables (no "entenderás X" sino "podrás hacer Y")
- Adaptar la carga al tiempo disponible indicado
## Restricciones
- No proponer más de 5-7 horas semanales salvo que el usuario pida más
- No recomendar recursos de pago sin alternativa gratuita
- Ser realista con los plazos
- Máximo 12 semanas por roadmap (si el tema requiere más, dividir en fases) 4. Explicador de Conceptos Complejos Le pasas un concepto denso y te lo explica con analogías, ejemplos cotidianos y niveles de profundidad que van de lo básico a lo avanzado. name: complex-concept-explainer
 description: Explica conceptos complejos usando analogías, ejemplos cotidianos y múltiples niveles de profundidad, desde explicación básica hasta detalle técnico.
---
# Explicador de Conceptos Complejos
## Resumen
Convierte conceptos difíciles en explicaciones comprensibles. Usa el método de capas: primero lo explica como si tuvieras 10 años, luego sube el nivel hasta la versión técnica completa.
**Palabras clave**: explicación, analogía, conceptos, simplificación, aprendizaje, niveles
## Características
- Explicación en 3 niveles (básico, intermedio, avanzado)
- Analogías con situaciones cotidianas
- Ejemplos prácticos del mundo real
- Identificación de errores comunes de comprensión
- Conexión con conceptos relacionados
## Formato de Salida
- Nivel 1 - Explicación simple (como para alguien sin contexto)
- Nivel 2 - Explicación intermedia (con terminología del campo)
- Nivel 3 - Explicación técnica (con detalle completo)
- Analogía principal
- Ejemplo práctico
- Errores comunes sobre este concepto
- Conceptos relacionados para seguir explorando
## Instrucciones
- Empezar SIEMPRE por la analogía o metáfora más intuitiva
- En el nivel 1, cero jerga técnica
- En el nivel 2, introducir terminología explicándola
- En el nivel 3, asumir que el lector ya maneja los fundamentos
- Incluir al menos un "lo que la gente suele confundir es..."
- Cerrar con conexiones a otros conceptos del mismo campo
## Restricciones
- No sacrificar precisión por simplicidad (simplificar ≠ falsear)
- Cada nivel debe ser autosuficiente (entendible sin leer los otros)
- Las analogías deben ser fieles al concepto, no forzadas 5. Redactor de Trabajos Académicos Estructura TFGs, ensayos y trabajos con formato académico: introducción, marco teórico, desarrollo, conclusiones y bibliografía. name: academic-paper-drafter
 description: Estructura y redacta trabajos académicos con formato estándar: introducción, marco teórico, desarrollo, conclusiones, citas y bibliografía.
---
# Redactor de Trabajos Académicos
## Resumen
Ayuda a estructurar y redactar trabajos académicos desde ensayos cortos hasta TFGs. Genera el esqueleto completo con secciones estándar y guía la redacción de cada parte.
**Palabras clave**: TFG, ensayo, trabajo académico, estructura, bibliografía, citas, universidad
## Características
- Estructura académica estándar
- Generación de introducción con justificación y objetivos
- Marco teórico con conceptos clave
- Desarrollo argumentativo coherente
- Conclusiones alineadas con los objetivos
- Formato de citas (APA, Harvard, Vancouver)
## Formato de Salida
- Título propuesto
- Índice / Estructura
- Introducción (contexto, justificación, objetivos, metodología)
- Marco teórico
- Desarrollo / Resultados
- Conclusiones
- Bibliografía (formato indicado)
## Instrucciones
- Preguntar el tipo de trabajo (ensayo, TFG, informe) y formato de citas requerido
- Generar estructura completa antes de redactar
- La introducción debe incluir: qué se investiga, por qué es relevante y cómo se aborda
- El desarrollo debe seguir un hilo argumentativo claro
- Las conclusiones deben responder directamente a los objetivos planteados
- Incluir placeholders para citas con formato [Autor, Año]
## Restricciones
- No inventar fuentes ni citas
- Marcar con [CITA NECESARIA] donde haga falta referencia
- No plagiar: todo debe ser redacción original
- Ajustar extensión al tipo de trabajo indicado
- Usar registro formal académico 6. Creador de Flashcards Extrae de apuntes o textos los pares pregunta-respuesta más importantes para repaso con repetición espaciada. name: flashcard-creator
 description: Extrae conceptos clave de apuntes o textos y genera flashcards pregunta-respuesta optimizadas para repaso con repetición espaciada.
---
# Creador de Flashcards
## Resumen
Convierte cualquier material de estudio en flashcards listas para usar. Genera pares pregunta-respuesta concisos, optimizados para memorización activa y repetición espaciada.
**Palabras clave**: flashcards, repaso, memorización, repetición espaciada, estudio, Anki
## Características
- Extracción automática de conceptos evaluables
- Pares pregunta-respuesta concisos
- Clasificación por dificultad
- Formato compatible con Anki / Quizlet
- Variedad de tipos: definición, ejemplo, comparación, aplicación
## Formato de Salida
- Lista de flashcards numeradas
- Cada flashcard:
 - FRENTE: Pregunta o prompt
 - REVERSO: Respuesta concisa
 - ETIQUETA: Tema + dificultad (fácil/medio/difícil)
## Instrucciones
- Analizar el material proporcionado
- Identificar datos, definiciones, procesos y relaciones evaluables
- Formular preguntas específicas (no vagas)
- Las respuestas deben ser de 1-3 líneas máximo
- Variar el tipo de pregunta: "¿Qué es...?", "¿Cuál es la diferencia entre...?", "¿Para qué sirve...?", "Ejemplo de..."
- Generar entre 15-30 flashcards por tema
- Ordenar de más fácil a más difícil
## Restricciones
- Las respuestas deben ser concisas (la gracia de las flashcards es la brevedad)
- No hacer preguntas que se respondan con sí/no
- No repetir el mismo concepto en varias tarjetas
- Cada tarjeta debe ser independiente (entendible sin las demás) 7. Planificador de Sesiones de Estudio Le dices cuántos días tienes, cuántas asignaturas y el nivel de dificultad, y te monta un calendario de estudio realista con descansos incluidos. name: study-session-planner
 description: Genera calendarios de estudio personalizados distribuyendo asignaturas, bloques de estudio, descansos y repasos según el tiempo disponible y la dificultad.
---
# Planificador de Sesiones de Estudio
## Resumen
Crea un plan de estudio realista y personalizado. Distribuye las asignaturas según dificultad, aplica técnicas de estudio probadas (Pomodoro, repaso espaciado) y genera un horario día a día.
**Palabras clave**: planificación, estudio, calendario, Pomodoro, repaso, exámenes, horario
## Características
- Distribución por dificultad y prioridad
- Bloques de estudio con técnica Pomodoro (25min+5min)
- Sesiones de repaso espaciado integradas
- Descansos y días libres planificados
- Adaptable a horas disponibles por día
## Formato de Salida
- Datos de entrada (días disponibles, asignaturas, dificultad)
- Calendario día a día con:
 - Asignatura del bloque
 - Duración y horario sugerido
 - Tipo de sesión (estudio nuevo / repaso / práctica)
 - Descansos marcados
- Consejos generales para la semana
## Instrucciones
- Preguntar: asignaturas, días disponibles, horas/día, fechas de exámenes
- Asignar más tiempo a las asignaturas más difíciles o con examen más próximo
- Alternar asignaturas para evitar fatiga mental
- Incluir sesiones de repaso de lo estudiado 1-2 días antes
- Planificar descansos de 5-10 min entre bloques y 30min entre asignaturas
- Reservar al menos medio día libre por semana
- Si hay más de 5 asignaturas, priorizar y rotar
## Restricciones
- No planificar más de 6 horas de estudio efectivo por día
- No poner la misma asignatura más de 2 horas seguidas
- Incluir siempre al menos 1 descanso largo
- Ser realista: si hay 3 días para 5 temas, decirlo 💼 Productividad Laboral 8. Redactor de Emails Profesionales Adapta tono según contexto: seguimiento, escalado, contacto frío, respuesta a queja... Va al grano y no suena a robot. name: professional-email-drafter
 description: Redacta emails profesionales adaptando tono, estructura y formalidad según el contexto: interno, cliente, proveedor, solicitud, seguimiento o escalado.
---
# Redactor de Emails Profesionales
## Resumen
Genera emails listos para enviar con el tono y estructura adecuados para cada situación laboral. Desde un seguimiento amable hasta un escalado firme.
**Palabras clave**: email, comunicación, profesional, tono, redacción, negocio
## Características
- Detección de contexto (seguimiento, solicitud, escalado, presentación, queja)
- Adaptación de tono (formal, cordial, directo, diplomático)
- Estructura clara: saludo, contexto, petición/propuesta, cierre
- Generación de asunto optimizado
- Variante alternativa de tono si el contexto es delicado
## Formato de Salida
- Asunto del email
- Cuerpo completo con saludo y despedida
- Variante alternativa si aplica
- Nota sobre el tono elegido y por qué
## Instrucciones
- Identificar el propósito del email
- Determinar la relación con el destinatario
- Elegir tono apropiado
- Estructurar con apertura breve, cuerpo claro y cierre con next step
- Mantener brevedad: máximo 150 palabras salvo que el contexto exija más
- Si es un seguimiento, referenciar la comunicación anterior
- Si es un escalado, mantener firmeza sin agresividad
## Restricciones
- No ser pasivo-agresivo
- No usar frases vacías tipo "espero que este email te encuentre bien" salvo que se pida
- Ir al grano
- No incluir excusas innecesarias 9. Organizador de Reuniones y Actas Convierte notas desordenadas de una reunión en un acta limpia con decisiones, tareas, responsables y deadlines. Para que nadie se vaya de una reunión sin saber qué tiene que hacer. name: meeting-notes-organizer
 description: Estructura notas de reunión en formato accionable con decisiones tomadas, tareas asignadas, responsables y fechas límite.
---
# Organizador de Reuniones y Actas
## Resumen
Convierte notas en bruto en un acta profesional con todo lo que importa: qué se decidió, quién hace qué y para cuándo.
**Palabras clave**: reunión, actas, notas, tareas, decisiones, seguimiento
## Características
- Extracción automática de decisiones y acuerdos
- Identificación de action items con responsable y deadline
- Resumen ejecutivo de la reunión
- Sección de temas pendientes para la próxima
## Formato de Salida
- Datos de la reunión (fecha, asistentes, tema)
- Resumen ejecutivo (3-5 líneas)
- Decisiones tomadas
- Action items (quién, qué, cuándo)
- Temas pendientes / para próxima reunión
## Instrucciones
- Procesar las notas en bruto
- Separar discusión de decisiones
- Extraer cada tarea con responsable y fecha
- Resumir en formato escaneable
- Si hay debates sin resolución, moverlos a "pendientes"
## Restricciones
- No inventar información que no esté en las notas
- Marcar con [PENDIENTE] cualquier acción sin responsable claro
- Marcar con [SIN FECHA] cualquier tarea sin deadline definido
- Priorizar claridad sobre exhaustividad 10. Optimizador de CV y LinkedIn Le pasas tu CV y la oferta a la que aplicas, y te lo adapta destacando lo relevante para ese puesto concreto. También optimiza tu perfil de LinkedIn. name: cv-linkedin-optimizer
 description: Adapta CV y perfiles de LinkedIn a ofertas de empleo específicas, destacando experiencia relevante, palabras clave del sector y logros cuantificables.
---
# Optimizador de CV y LinkedIn
## Resumen
Toma tu CV actual y la oferta a la que quieres aplicar, y reescribe la experiencia para que encaje con lo que buscan. También genera sugerencias para tu perfil de LinkedIn.
**Palabras clave**: CV, currículum, LinkedIn, empleo, candidatura, ATS, palabras clave
## Características
- Análisis de la oferta de empleo (requisitos clave)
- Reescritura de experiencia alineada al puesto
- Inclusión de palabras clave para pasar filtros ATS
- Cuantificación de logros
- Sugerencias para headline y about de LinkedIn
- Detección de gaps y cómo abordarlos
## Formato de Salida
- CV optimizado con secciones:
 - Perfil profesional (3-4 líneas)
 - Experiencia (adaptada al puesto)
 - Habilidades (priorizadas según oferta)
 - Formación
- Sugerencias LinkedIn:
 - Headline optimizado
 - Resumen / About
 - Habilidades a destacar
## Instrucciones
- Analizar la oferta de empleo e identificar las 5-7 competencias clave
- Mapear la experiencia del usuario contra esas competencias
- Reescribir las descripciones de puesto usando verbos de acción y resultados medibles
- Incluir keywords de la oferta de forma natural
- Para LinkedIn, optimizar el headline con puesto + valor diferencial
- Si falta experiencia directa en algo, sugerir cómo presentar experiencia transferible
## Restricciones
- No inventar experiencia ni inflar logros
- No hacer el CV de más de 2 páginas (1 si hay menos de 5 años de experiencia)
- No copiar frases textuales de la oferta
- Mantener honestidad: si hay un gap importante, señalarlo y sugerir cómo abordarlo 11. Preparador de Presentaciones Un tema o briefing → estructura de presentación con puntos por slide, narrativa, datos clave y sugerencia visual para cada diapositiva. name: presentation-prep-skill
 description: Estructura presentaciones completas con narrativa, puntos clave por slide, sugerencias visuales y notas del ponente.
---
# Preparador de Presentaciones
## Resumen
Convierte un tema, briefing o documento en una presentación estructurada slide por slide. Incluye qué decir, qué mostrar y cómo mantener la atención de la audiencia.
**Palabras clave**: presentación, slides, PowerPoint, narrativa, ponencia, pitch, estructura
## Características
- Estructura narrativa completa (apertura, desarrollo, cierre)
- Contenido por slide (título, puntos, visual sugerido)
- Notas del ponente para cada slide
- Timing estimado
- Hook de apertura y cierre memorable
## Formato de Salida
- Título de la presentación
- Audiencia objetivo
- Duración estimada
- Estructura slide por slide:
 - Número de slide
 - Título
 - Puntos clave (máximo 3-4 por slide)
 - Visual sugerido (gráfico, imagen, diagrama, cita)
 - Notas del ponente (qué decir)
 - Tiempo estimado
## Instrucciones
- Empezar con un hook que capte atención (dato sorprendente, pregunta, historia)
- Seguir la regla de 1 idea = 1 slide
- Máximo 3-4 puntos por slide (el slide apoya, no sustituye al ponente)
- Incluir un slide de transición entre secciones grandes
- Cerrar con call to action o mensaje memorable
- Sugerir visuales concretos, no genéricos ("gráfico de barras comparando X vs Y", no "algún gráfico")
- Añadir timing estimado por slide
## Restricciones
- No más de 20 slides para presentaciones de 15-20 minutos
- No slides de solo texto (cada slide debe tener componente visual)
- Las notas del ponente no deben ser un guion literal, sino puntos clave
- Evitar slides con más de 30 palabras 🔍 Investigación y Análisis 12. Sintetizador de Investigación Profunda Convierte grandes cantidades de información en insights estructurados y conclusiones accionables. Filtra el ruido y se queda con lo que importa. name: deep-research-synthesizer
 description: Sintetiza insights de grandes conjuntos de datos, filtra información irrelevante, identifica patrones y produce resúmenes accionables.
---
# Sintetizador de Investigación Profunda
## Resumen
Convierte grandes cantidades de texto en insights estructurados y conclusiones accionables.
**Palabras clave**: investigación, síntesis, insights, análisis, conocimiento
## Características
- Filtra información de bajo valor
- Destaca patrones
- Crea salida estructurada
## Formato de Salida
- Insights clave
- Detalles de soporte
- Párrafo de resumen
## Instrucciones
- Identificar puntos clave
- Eliminar contenido irrelevante
- Organizar lógicamente
## Restricciones
- Evitar resúmenes genéricos
- Enfocarse en utilidad 13. Validación de Fuentes Filtra información por fiabilidad. Evalúa si una fuente es creíble, detecta sesgos y te dice en qué puedes confiar. name: source-validation-skill
 description: Valida la credibilidad de fuentes de información, destacando fiabilidad, relevancia y posibles sesgos.
---
# Skill de Validación de Fuentes
## Resumen
Filtra información por fiabilidad y relevancia.
**Palabras clave**: credibilidad, validación, fuentes, investigación, sesgo
## Características
- Puntuación de fiabilidad
- Detección de sesgos
- Filtrado de relevancia
## Formato de Salida
- Fuentes verificadas
- Insights clave
- Notas sobre fiabilidad
## Instrucciones
- Comprobar referencias
- Evaluar autor y fecha
- Destacar contenido fiable
## Restricciones
- Evitar información no verificada
- Priorizar fuentes de alta calidad 14. Estructuración de Conocimiento Transforma información desordenada en frameworks claros y usables. Ideal cuando tienes muchas notas sueltas y necesitas darles estructura. name: knowledge-structuring-skill
 description: Organiza información desestructurada en frameworks claros, puntos y notas estructuradas para facilitar comprensión y aplicación.
---
# Skill de Estructuración de Conocimiento
## Resumen
Transforma input desordenado en conocimiento estructurado y usable.
**Palabras clave**: conocimiento, estructuración, frameworks, organización, notas
## Características
- Categoriza ideas
- Crea jerarquía lógica
- Formato en viñetas
## Formato de Salida
- Framework estructurado
- Puntos clave
- Notas opcionales
## Instrucciones
- Identificar temas principales
- Agrupar ideas relacionadas
- Presentar de forma clara y concisa
## Restricciones
- Evitar ambigüedad
- Mantener legibilidad 15. Inteligencia Competitiva Compara productos, herramientas o servicios de forma estructurada. Fortalezas, debilidades, oportunidades y recomendaciones. name: competitive-intelligence-skill
 description: Compara productos, herramientas o servicios proporcionando análisis estructurado de fortalezas, debilidades y oportunidades.
---
# Skill de Inteligencia Competitiva
## Resumen
Ofrece insights comparativos para investigación de negocio, tecnología o mercado.
**Palabras clave**: análisis, competitivo, investigación, comparación, estrategia
## Características
- Comparación de características
- Análisis tipo DAFO
- Recomendaciones
## Formato de Salida
- Comparación en puntos
- Fortalezas/debilidades
- Conclusiones clave
## Instrucciones
- Identificar competidores/herramientas
- Comparar características
- Destacar diferencias y riesgos
## Restricciones
- Evitar sesgos
- Enfocarse en insights accionables 🎬 Vídeo y Contenido Visual 16. Generador de Guiones de Vídeo Produce guiones estructurados para vídeo corto y largo con hooks, secciones claras, ritmo controlado y CTAs. name: video-script-generator
 description: Genera guiones de vídeo con hooks, secciones estructuradas, ritmo y llamadas a la acción optimizados para engagement y retención.
---
# Generador de Guiones de Vídeo
## Resumen
Produce guiones estructurados para contenido de vídeo corto y largo.
**Palabras clave**: vídeo, guiones, hooks, engagement, ritmo, contenido
## Características
- Hooks de apertura potentes
- Contenido por secciones
- Llamadas a la acción claras
## Formato de Salida
- Hook
- Secciones de contenido
- Resumen de cierre
## Instrucciones
- Empezar con hook
- Organizar puntos principales
- Mantener ritmo
- Incluir CTA
## Restricciones
- Evitar relleno
- Mantener la atención de la audiencia 17. Generador de Hooks Crea aperturas que captan la atención en los primeros segundos. Para vídeos, posts, hilos o cualquier contenido donde los primeros 3 segundos deciden si te leen o te ignoran. name: hook-generator
 description: Produce hooks que captan atención para vídeos, posts de redes sociales e intros de contenido para maximizar el engagement.
---
# Generador de Hooks
## Resumen
Crea aperturas convincentes para captar la atención inmediatamente.
**Palabras clave**: hook, atención, engagement, intro, viral
## Características
- Corto, impactante
- Basado en curiosidad
- Adaptable al tipo de contenido
## Formato de Salida
- Frase hook
- Intro de seguimiento opcional
## Instrucciones
- Enfocarse en curiosidad o afirmaciones potentes
- Mantener concisión
- Coincidir con el interés de la audiencia
## Restricciones
- Evitar hooks genéricos
- Mantener relevancia 18. Constructor de Diagramas de Flujo Convierte procesos en diagramas de flujo paso a paso con nodos, ramificaciones condicionales y rutas claras. name: flowchart-decision-builder
 description: Genera árboles de decisión y diagramas de flujo a partir de texto para simplificar procesos complejos de toma de decisiones.
---
# Constructor de Diagramas de Flujo
## Resumen
Convierte procesos en diagramas de flujo para toma de decisiones clara.
**Palabras clave**: diagrama de flujo, árbol de decisión, proceso, visualización, claridad
## Características
- Estructura basada en nodos
- Ramificación condicional
- Etiquetado claro
## Formato de Salida
- Nodos
- Conexiones
- Guía de layout
## Instrucciones
- Identificar pasos y decisiones
- Mapear caminos condicionales
- Mantener flujo lógico
## Restricciones
- Mantener diagramas simples
- Evitar nodos innecesarios 💻 Código y Automatización 19. Documentador de Código Le pasas una función, clase o módulo y te genera documentación clara con descripción, parámetros, tipos de retorno, ejemplos de uso y edge cases. Para que no vuelvas a dejar una función sin documentar. name: code-documenter
 description: Genera documentación técnica clara a partir de funciones, clases o módulos, incluyendo descripción, parámetros, tipos de retorno, ejemplos de uso y edge cases.
---
# Documentador de Código
## Resumen
Convierte código sin documentar en documentación profesional. Analiza la firma, la lógica interna y los posibles casos límite para generar docs completas y útiles.
**Palabras clave**: documentación, código, funciones, JSDoc, docstrings, API, parámetros
## Características
- Descripción clara de qué hace el código
- Listado de parámetros con tipos y descripción
- Tipo de retorno documentado
- Ejemplos de uso funcionales
- Edge cases y errores posibles identificados
- Formato adaptable (JSDoc, docstrings Python, TSDoc, Javadoc)
## Formato de Salida
- Bloque de documentación en el formato del lenguaje
- Sección de ejemplos de uso
- Notas sobre edge cases o limitaciones
## Instrucciones
- Analizar la función/módulo completo
- Identificar cada parámetro, su tipo y si es opcional
- Describir qué hace en una frase clara (no repetir el nombre)
- Generar al menos 2 ejemplos de uso (caso normal + caso especial)
- Listar edge cases: valores nulos, arrays vacíos, tipos inesperados
- Adaptar el formato al lenguaje del código (Python → docstrings, JS/TS → JSDoc/TSDoc)
## Restricciones
- No inventar comportamientos que no estén en el código
- No documentar lo obvio ("esta función hace lo que dice el nombre")
- Cada parámetro debe tener tipo y descripción
- Los ejemplos deben ser ejecutables 20. Generador de Tests Unitarios Analiza tu código y genera tests automáticos cubriendo casos normales, edge cases y manejo de errores. Compatible con los frameworks de testing más usados. name: unit-test-generator
 description: Analiza funciones o módulos y genera tests unitarios completos cubriendo happy paths, edge cases y manejo de errores para los principales frameworks de testing.
---
# Generador de Tests Unitarios
## Resumen
Toma cualquier función o módulo y genera una suite de tests que cubre los caminos principales, los casos límite y los errores esperados. Te ahorra la parte más tediosa del desarrollo.
**Palabras clave**: tests, testing, unitarios, jest, pytest, vitest, edge cases, cobertura
## Características
- Tests para happy path (caso normal)
- Tests para edge cases (valores límite, vacíos, nulos)
- Tests para manejo de errores
- Mocks y stubs cuando sea necesario
- Adaptable al framework (Jest, Vitest, Pytest, JUnit, Mocha)
## Formato de Salida
- Archivo de tests completo y ejecutable
- Organizado por describe/it o equivalente
- Comentarios explicando qué testea cada bloque
## Instrucciones
- Analizar la función y sus inputs/outputs
- Identificar todos los caminos posibles del código
- Generar al menos: 2 tests happy path, 2 edge cases, 1 test de error
- Si la función tiene dependencias externas, mockearlas
- Usar nombres descriptivos: "should return X when Y"
- Añadir comentarios breves sobre por qué cada test importa
## Restricciones
- Los tests deben ser ejecutables sin modificación
- No testear implementación interna, solo comportamiento
- Cada test debe ser independiente (no depender del orden)
- Usar el framework que corresponda al lenguaje del código fuente 21. Debugger Asistente Le pegas un error y tu código, y te guía paso a paso hasta encontrar el problema y la solución. Como hacer pair programming con alguien que no se cansa. name: debug-assistant
 description: Analiza errores de código junto con el contexto del programa, identifica la causa raíz paso a paso y propone soluciones concretas con explicación.
---
# Debugger Asistente
## Resumen
Recibe un mensaje de error y el código relevante, y te guía desde el síntoma hasta la causa raíz con una solución concreta. No solo te dice qué poner, sino por qué falló.
**Palabras clave**: debug, error, bug, fix, stack trace, solución, diagnóstico
## Características
- Análisis del mensaje de error y stack trace
- Identificación de la causa raíz (no solo el síntoma)
- Explicación paso a paso del problema
- Solución concreta con código corregido
- Prevención: cómo evitar ese error en el futuro
## Formato de Salida
- Diagnóstico: qué dice el error y qué significa realmente
- Causa raíz: por qué ocurre
- Solución: código corregido
- Prevención: tip para que no vuelva a pasar
## Instrucciones
- Leer el error completo (mensaje + stack trace si hay)
- Localizar la línea exacta del fallo
- Analizar el contexto: variables, tipos, flujo de ejecución
- Explicar la causa en lenguaje claro (no repetir el error textual)
- Proponer la solución mínima que resuelva el problema
- Si hay varias causas posibles, listarlas de más a menos probable
- Incluir un tip de prevención
## Restricciones
- No reescribir todo el código, solo lo necesario
- Siempre explicar el POR QUÉ, no solo el QUÉ
- Si falta contexto para diagnosticar, pedir el código o datos que faltan
- No asumir el framework/versión: preguntar si es ambiguo
 22. Constructor de Regex con Explicación Describes qué quieres validar o extraer en lenguaje normal y te genera la expresión regular con una explicación detallada de cada parte. No más regex copiadas de Stack Overflow sin entenderlas. name: regex-builder-explainer
 description: Genera expresiones regulares a partir de descripciones en lenguaje natural, con explicación paso a paso de cada componente y ejemplos de coincidencia.
---
# Constructor de Regex con Explicación
## Resumen
Traduce lo que necesitas validar o extraer a una expresión regular funcional, explicando qué hace cada parte. También puede tomar una regex existente y explicarla.
**Palabras clave**: regex, expresión regular, validación, extracción, patrones, parsing
## Características
- Generación de regex desde lenguaje natural
- Explicación componente por componente
- Ejemplos de strings que coinciden y que no
- Soporte para diferentes sabores (JS, Python, PHP, Go)
- Modo inverso: recibe una regex y la explica
## Formato de Salida
- Regex completa
- Desglose por partes con explicación
- Ejemplos: 3 strings que hacen match, 2 que no
- Notas sobre el sabor/motor de regex usado
## Instrucciones
- Identificar exactamente qué se quiere validar/extraer
- Construir la regex de forma progresiva (de simple a completa)
- Explicar cada grupo, cuantificador y metacarácter
- Probar mentalmente con ejemplos positivos y negativos
- Si hay varias formas de hacerlo, usar la más legible
- Indicar si la regex necesita flags (g, i, m, etc.)
## Restricciones
- Priorizar legibilidad sobre brevedad
- No usar lookaheads/lookbehinds salvo que sea necesario
- Indicar limitaciones de la regex (qué NO cubre)
- Especificar siempre el motor/sabor de regex 23. Generador de Commits Convencionales Analiza los cambios de tu código y escribe mensajes de commit descriptivos siguiendo el estándar Conventional Commits. Para que tu historial de git deje de ser un caos de "fix things" y "update stuff". name: conventional-commit-generator
 description: Analiza cambios de código y genera mensajes de commit descriptivos siguiendo el estándar Conventional Commits con tipo, scope, descripción y body opcional.
---
# Generador de Commits Convencionales
## Resumen
Toma un diff, una descripción de cambios o una lista de archivos modificados y genera mensajes de commit profesionales siguiendo Conventional Commits.
**Palabras clave**: git, commit, conventional commits, versionado, changelog, historial
## Características
- Formato Conventional Commits (type(scope): description)
- Detección automática del tipo (feat, fix, refactor, docs, style, test, chore)
- Scope inferido del contexto
- Body opcional para cambios complejos
- Breaking changes detectados y marcados
- Múltiples commits si los cambios son independientes
## Formato de Salida
- Mensaje de commit formateado:
 - Línea 1: type(scope): descripción concisa
 - Línea 3+: body explicativo (si el cambio lo requiere)
 - Footer: BREAKING CHANGE si aplica
## Instrucciones
- Analizar los cambios proporcionados (diff, lista o descripción)
- Determinar el tipo principal: feat (nueva funcionalidad), fix (corrección), refactor (sin cambio de comportamiento), docs, style, test, chore
- Inferir el scope del área afectada (auth, api, ui, db, etc.)
- Escribir descripción en imperativo, minúscula, sin punto final, máximo 72 caracteres
- Si hay múltiples cambios no relacionados, proponer commits separados
- Añadir body solo si el "qué" no es obvio sin el "por qué"
## Restricciones
- Máximo 72 caracteres en la primera línea
- Imperativo: "add" no "added", "fix" no "fixed"
- Un commit = un cambio lógico
- No mezclar feat + fix en el mismo commit
- Si no hay suficiente contexto, preguntar antes de asumir el tipo
 24. Skill de Revisión de Código Analiza código en busca de bugs, ineficiencias y malas prácticas. Devuelve problemas detectados con sugerencias concretas de mejora. name: code-review-skill
 description: Revisa código en busca de bugs, ineficiencias y adherencia a buenas prácticas, proporcionando sugerencias de mejora accionables.
---
# Skill de Revisión de Código
## Resumen
Analiza código para asegurar calidad, eficiencia y mantenibilidad.
**Palabras clave**: código, revisión, bugs, optimización, buenas prácticas
## Características
- Detección de errores
- Recomendaciones de optimización
- Aplicación de estilo
## Formato de Salida
- Problemas encontrados
- Correcciones sugeridas
- Resumen opcional
## Instrucciones
- Analizar código línea por línea
- Destacar errores o ineficiencias
- Sugerir mejoras
## Restricciones
- Mantener precisión
- Evitar falsos positivos 25. Agente de Automatización de Flujos de Trabajo Descompone cualquier objetivo complejo en un flujo de trabajo paso a paso, asigna herramientas a cada paso y optimiza la ejecución. name: workflow-automation-agent
 description: Descompone tareas complejas en flujos de trabajo paso a paso, mapeando acciones a herramientas, optimizando ejecución y mejorando eficiencia.
---
# Agente de Automatización de Flujos de Trabajo
## Resumen
Convierte objetivos en flujos de trabajo accionables para ejecución asistida por IA o humana.
**Palabras clave**: automatización, flujo de trabajo, productividad, pasos, ejecución
## Características
- Descomposición de tareas
- Mapeo de herramientas
- Optimización
## Formato de Salida
- Objetivo
- Acciones paso a paso
- Herramientas e instrucciones
## Instrucciones
- Identificar objetivo
- Descomponer en pasos
- Asignar herramientas
- Optimizar para eficiencia
## Restricciones
- Evitar instrucciones vagas
- Mantener flujo lógico Cómo añadir estas skills Cada skill está en formato .md. Para usarlas: En Claude : Puedes añadirlas como parte de un Proyecto o pegarlas directamente en la conversación como contexto. En ChatGPT : Copia el contenido del bloque de código y pégalo como instrucción al inicio de tu conversación o en las instrucciones personalizadas. En Gemini : Pega el contenido como prompt de sistema o contexto previo a tu consulta. La gracia de tener skills en .md es que son modulares: las cargas solo cuando las necesitas, y puedes combinar varias en la misma sesión.```

---

*このログは `X.htm`（およびそのリソースフォルダ `X_files/`）から自動抽出したものです。画像資産は `X_files/HIDR2yGXsAADN1b_esQY.jpg`（記事内の一覧画像）にあります。*

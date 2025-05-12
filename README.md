## RAG-Evaluation

In vielen Anwendungsbereichen ist der schnelle Zugriff auf domänenspezifisches Wissen über Chatbots von wachsender Bedeutung. Retrieval-Augmented Generation (RAG) kombiniert Large Language Models (LLMs) mit gezieltem Informationsabruf aus externen Dokumenten und bietet damit eine effektive Lösung für wissensintensive Aufgaben. Ziel dieses Projekt ist die Entwicklung eines automatisierten Frameworks zur Evaluation der Antwortqualität RAG-gestützter Systeme.

### **Methodik**

* **Daten:** 
  - Verarbeitung unstrukturierter Dokumente
  - Embedding  
  - Speicherung im Vektorindex
* **Retrieval:** Vergleich verschiedene Retrieval-Strategien
* **Generierung:** Test verschiedener LLMs (z.B. GPT-4, Claude, LLaMA) mit angepasstem Prompting
* **Evaluation:** Automatisierte Bewertung durch Metriken wie Context Precision, Faithfulness und Relevanz – ergänzt durch LLM-basierte Bewertungen (LLM-as-a-Judge)
* **Experimente:** Systematische Auswertung und Versionierung mittels MLflow
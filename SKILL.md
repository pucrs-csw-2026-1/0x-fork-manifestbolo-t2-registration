---
name: adr-creator
description: "How to create Architecture Decision Records (ADRs). Use this skill whenever the user wants to document a decision, mentions ADRs, asks to 'create an ADR', or needs to formalize architectural choices. It helps find the right folder, determine the next sequential number, and uses the standard project ADR template."
---

# ADR Creator

A skill to help the user document Architectural Decision Records (ADRs) in the correct format and location within the project.

## When to use this skill

Use this skill when the user wants to document a new system decision or architecture change. Even if the user just asks to "document this decision", you should suggest making an ADR.

## Steps to create an ADR

1. **Identify the target directory**:
   - Determine if the decision is for the `frontend` or the `backend`.
   - The corresponding ADR directories are:
     - Frontend: `frontend/documentation/adrs/`
     - Backend: `backend/documentation/adrs/`
   - If the directory does not exist, you must create it.

2. **Determine the next ADR number**:
   - Use listing tools (`ls` or `list_dir`) on the target directory to find the existing ADR files.
   - Files are prefixed with a 4-digit number (e.g., `0001-nome-da-decisao.md`).
   - Find the highest number and increment it by 1 to get the new number. If no ADRs exist, start at `0001`.

3. **Format the file name**:
   - The file name should be in lowercase, words separated by hyphens, without special characters.
   - Format: `[4-digit-number]-[kebab-case-title].md` (e.g., `0004-adotar-react-query.md`).

4. **Write the content using the standard template**:
   - Always write the generated content for the ADRs entirely in Brazilian Portuguese (pt-BR), as per the project standard.
   - You MUST use the exact following Markdown template:

```markdown
# [Número]. [Título da Decisão]

**Data:** AAAA-MM-DD

## Status

[Proposto | Aceito | Substituído | Depreciado]

## Contexto

Descreva o problema ou situação que levou à necessidade de uma decisão.
Inclua restrições técnicas, requisitos de negócio e alternativas consideradas.

## Decisão

Descreva claramente a decisão tomada e por quê.

## Consequências

- **Positivo:** Benefícios esperados
- **Negativo:** Trade-offs ou riscos conhecidos
```

1. **Review with the user**:
   - Create the file and present the summary to the user.

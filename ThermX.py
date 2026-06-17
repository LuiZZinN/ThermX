;; ====================================================================
;; Script ANSYS Fluent Meshing (TUI) - Corrigido e Alinhado com o CFD
;; ====================================================================

;; 1. Importação do CAD Geométrico
/file/import/cad "TrocadorCalor_Geometria.STEP"

;; 2. Configuração e Geração Obrigatória da Malha de Superfície (Surface Mesh)
/objects/scoped-sizing/create curvature-size curvature global-lengths 1.0 5.0 1.2
/mesh/surface-mesh/draw-and-mesh

;; 3. Definição dos Escopos de Camadas de Prisma (Boundary Layer)
;; Comando moderno para gerenciar o crescimento geométrico global dos prismas
/mesh/scoped-prisms/set-growth-options geometric 12 1.2

;; Lado Interno: Alinhado com o relatório (dy para y+=35) -> 8.6228e-05 m
/mesh/scoped-prisms/create/specified-first-height internal_prisms tube_walls_internal face-zones "tube_walls_internal" 8.6228e-05

;; Lado Externo: Alinhado com o relatório (dy para y+=1) -> 9.9223e-05 m
/mesh/scoped-prisms/create/specified-first-height external_prisms tube_walls_external face-zones "tube_walls_external" 9.9223e-05

;; 4. Geração das Camadas de Prisma nas Paredes Scoped
/mesh/scoped-prisms/grow

;; 5. Inicialização e Geração da Malha Volumétrica Poliédrica
;; Primeiro o Fluent inicializa o volume a partir das superfícies e prismas
/mesh/volume/initialize
/mesh/volume/polyhedra

;; 6. Otimização de Qualidade e Exportação do Arquivo Final
/mesh/repair/improve-quality
/file/write-mesh "TrocadorCalor_Malha.msh"

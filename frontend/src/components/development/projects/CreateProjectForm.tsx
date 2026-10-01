import type { ReactNode } from "react";
import { Box, Check, Folder, History, Plus, Sparkles } from "lucide-react";

import type {
  CreateDevelopmentProjectOptions,
  OriginRobot,
  OriginRobotFolder,
  ProjectOriginMode,
} from "../../../types/development";

import useDevelopmentTemplates from "../../../hooks/development/useDevelopmentTemplates";

import { Button } from "../../ui/Button";
import FeedbackBanner from "../../ui/FeedbackBanner";
import { TextAreaField } from "../../ui/TextAreaField";
import { TextField } from "../../ui/TextField";


interface CreateProjectFormProps {

  originMode: ProjectOriginMode;

  baseRobotId: string;

  folders: OriginRobotFolder[];

  robots: OriginRobot[];

  selectedFolderId: number | null;

  robotsError: string;

  projectName: string;

  projectDescription: string;

  creating: boolean;

  onOriginModeChange:
    (mode: ProjectOriginMode) => void;

  onBaseRobotChange:
    (robotId: string) => void;

  onSelectedFolderChange:
    (folderId: number | null) => void;

  onProjectNameChange:
    (value: string) => void;

  onProjectDescriptionChange:
    (value: string) => void;

  onCancel:
    () => void;

  onCreate:
    (
      options?: CreateDevelopmentProjectOptions
    ) => void | Promise<void>;
}


export default function CreateProjectForm({
  originMode,
  baseRobotId,
  folders,
  robots,
  selectedFolderId,
  robotsError,
  projectName,
  projectDescription,
  creating,
  onOriginModeChange,
  onBaseRobotChange,
  onSelectedFolderChange,
  onProjectNameChange,
  onProjectDescriptionChange,
  onCancel,
  onCreate,
}: CreateProjectFormProps) {

  // ==========================================================
  // ROBOT PUBLICADO
  // ==========================================================

  const selectedRobot =
    robots.find(
      (robot) =>
        String(robot.id) ===
        baseRobotId
    ) ?? null;


  const robotsInSelectedFolder =
    robots.filter(
      (robot) =>
        robot.folder_id ===
        selectedFolderId
    );


  // ==========================================================
  // TEMPLATE
  // ==========================================================
  //
  // O carregamento fica isolado em um hook próprio para não
  // adicionar estado de Template em Development.tsx.
  //
  // O hook só carrega o catálogo quando a origem selecionada
  // realmente for "template".
  // ==========================================================

  const {
    templates,
    loadingTemplates,
    templatesError,

    selectedTemplateId,
    selectedTemplateVersionId,

    selectedTemplate,
    selectedTemplateVersion,

    selectTemplate,
    selectTemplateVersion,
  } =
    useDevelopmentTemplates(
      originMode === "template"
    );


  // ==========================================================
  // VALIDAÇÃO PARA CRIAR
  // ==========================================================

  const createDisabled =
    !projectName.trim() ||
    creating ||
    (
      originMode === "existing" &&
      !baseRobotId
    ) ||
    (
      originMode === "template" &&
      !selectedTemplateVersionId
    );


  // ==========================================================
  // CAMINHO DE ROBÔS
  // ==========================================================

  const getFolderPath =
    (
      folderId: number | null
    ): string => {

      if (
        folderId === null
      ) {
        return "Raiz de Robôs";
      }


      const names: string[] =
        [];


      const visited =
        new Set<number>();


      let currentId:
        number | null =
          folderId;


      while (
        currentId !== null &&
        !visited.has(
          currentId
        )
      ) {

        visited.add(
          currentId
        );


        const folder =
          folders.find(
            (item) =>
              item.id ===
              currentId
          );


        if (!folder) {
          break;
        }


        names.unshift(
          folder.name
        );


        currentId =
          folder.parent_id;
      }


      return [
        "Raiz de Robôs",
        ...names,
      ].join(" / ");
    };


  const chooseFolder =
    (
      folderId: number | null
    ) => {

      onSelectedFolderChange(
        folderId
      );


      onBaseRobotChange(
        ""
      );
    };


  const renderFolderTree =
    (
      parentId: number | null
    ): ReactNode[] =>
      folders
        .filter(
          (folder) =>
            folder.parent_id ===
            parentId
        )
        .sort(
          (
            left,
            right
          ) =>
            left.name.localeCompare(
              right.name,
              "pt-BR"
            )
        )
        .map(
          (folder) => (
            <div
              className="project-folder-node"
              key={folder.id}
            >
              <button
                type="button"
                aria-pressed={
                  selectedFolderId ===
                  folder.id
                }
                disabled={creating}
                onClick={() =>
                  chooseFolder(
                    folder.id
                  )
                }
              >
                <Folder
                  size={15}
                  aria-hidden="true"
                />

                <span>
                  {folder.name}
                </span>
              </button>

              <div className="project-folder-children">
                {renderFolderTree(
                  folder.id
                )}
              </div>
            </div>
          )
        );


  // ==========================================================
  // SUBMIT
  // ==========================================================

  const submitProject =
    async () => {

      if (createDisabled) {
        return;
      }


      if (
        originMode ===
        "template"
      ) {

        const options:
          CreateDevelopmentProjectOptions =
            {
              templateVersionId:
                Number(
                  selectedTemplateVersionId
                ),
            };


        await onCreate(
          options
        );

        return;
      }


      await onCreate();
    };


  return (
    <form
      className="project-create-panel"
      onSubmit={(event) => {

        event.preventDefault();

        void submitProject();
      }}
    >

      <header className="project-create-panel__header">

        <div>

          <span className="project-create-panel__eyebrow">
            Novo workspace
          </span>

          <h2>
            Crie um projeto de automação
          </h2>

          <p>
            Comece do zero, use um Template ou evolua uma versão publicada.
          </p>

        </div>


        <div
          className="project-create-panel__progress"
          aria-label="Duas etapas"
        >

          <span className="is-active">
            1
            {" "}
            <small>
              Origem
            </small>
          </span>

          <i aria-hidden="true" />

          <span
            className={
              projectName.trim()
                ? "is-active"
                : ""
            }
          >
            2
            {" "}
            <small>
              Demanda
            </small>
          </span>

        </div>

      </header>


      <div className="project-create-panel__body">

        <fieldset className="project-origin-fieldset">

          <legend>
            Escolha a origem
          </legend>


          <div className="project-origin-options">

            <button
              type="button"
              aria-pressed={
                originMode ===
                "new"
              }
              disabled={creating}
              onClick={() => {

                onOriginModeChange(
                  "new"
                );

                onBaseRobotChange(
                  ""
                );

                onSelectedFolderChange(
                  null
                );
              }}
            >

              <span className="project-origin-option__icon">
                <Sparkles
                  size={17}
                  aria-hidden="true"
                />
              </span>

              <span>

                <strong>
                  Nova automação
                </strong>

                <small>
                  Workspace limpo para começar uma solução inédita.
                </small>

              </span>

              {
                originMode ===
                "new" &&
                (
                  <Check
                    size={16}
                    className="project-origin-option__check"
                    aria-hidden="true"
                  />
                )
              }

            </button>


            <button
              type="button"
              aria-pressed={
                originMode ===
                "template"
              }
              disabled={creating}
              onClick={() => {

                onOriginModeChange(
                  "template"
                );

                onBaseRobotChange(
                  ""
                );

                onSelectedFolderChange(
                  null
                );
              }}
            >

              <span className="project-origin-option__icon">
                <Box
                  size={17}
                  aria-hidden="true"
                />
              </span>

              <span>

                <strong>
                  Usar Template
                </strong>

                <small>
                  Comece com uma estrutura de código já preparada.
                </small>

              </span>

              {
                originMode ===
                "template" &&
                (
                  <Check
                    size={16}
                    className="project-origin-option__check"
                    aria-hidden="true"
                  />
                )
              }

            </button>


            <button
              type="button"
              aria-pressed={
                originMode ===
                "existing"
              }
              disabled={creating}
              onClick={() =>
                onOriginModeChange(
                  "existing"
                )
              }
            >

              <span className="project-origin-option__icon">
                <History
                  size={17}
                  aria-hidden="true"
                />
              </span>

              <span>

                <strong>
                  Evoluir robô publicado
                </strong>

                <small>
                  Recupere código e bibliotecas de uma versão existente.
                </small>

              </span>

              {
                originMode ===
                "existing" &&
                (
                  <Check
                    size={16}
                    className="project-origin-option__check"
                    aria-hidden="true"
                  />
                )
              }

            </button>

          </div>

        </fieldset>


        {/* ====================================================
            TEMPLATE
        ==================================================== */}

        {
          originMode ===
          "template" &&
          (
            <section
              className="project-origin-browser"
              aria-label="Selecionar Template"
            >

              <div className="project-origin-browser__folders">

                <div className="project-origin-browser__title">

                  <span>
                    Templates
                  </span>

                  <small>
                    {
                      loadingTemplates
                        ? "Carregando..."
                        : `${templates.length} disponíveis`
                    }
                  </small>

                </div>


                {
                  !loadingTemplates &&
                  templates.length === 0
                    ? (
                      <div className="project-origin-browser__empty">

                        <Box
                          size={20}
                          aria-hidden="true"
                        />

                        <strong>
                          Nenhum Template disponível
                        </strong>

                        <span>
                          Cadastre um Template para utilizar esta origem.
                        </span>

                      </div>
                    )
                    : (
                      templates.map(
                        (template) => {

                          const selected =
                            String(
                              template.id
                            ) ===
                            selectedTemplateId;


                          return (
                            <button
                              key={
                                template.id
                              }
                              type="button"
                              className="project-folder-root"
                              aria-pressed={
                                selected
                              }
                              disabled={
                                creating
                              }
                              onClick={() =>
                                selectTemplate(
                                  String(
                                    template.id
                                  )
                                )
                              }
                            >

                              <Box
                                size={15}
                                aria-hidden="true"
                              />

                              <span>
                                {template.name}
                              </span>

                            </button>
                          );
                        }
                      )
                    )
                }

              </div>


              <div className="project-origin-browser__robots">

                <div className="project-origin-browser__title">

                  <span>
                    Versões
                  </span>

                  <small>
                    {
                      selectedTemplate
                        ? selectedTemplate.name
                        : "Selecione um Template"
                    }
                  </small>

                </div>


                {
                  !selectedTemplate
                    ? (
                      <div className="project-origin-browser__empty">

                        <Box
                          size={20}
                          aria-hidden="true"
                        />

                        <strong>
                          Selecione um Template
                        </strong>

                        <span>
                          A versão atual será selecionada automaticamente.
                        </span>

                      </div>
                    )
                    : (
                      <div className="project-origin-robot-list">

                        {
                          [...selectedTemplate.versions]
                            .sort(
                              (
                                left,
                                right
                              ) =>
                                right.version -
                                left.version
                            )
                            .map(
                              (version) => {

                                const selected =
                                  String(
                                    version.id
                                  ) ===
                                  selectedTemplateVersionId;


                                return (
                                  <button
                                    key={
                                      version.id
                                    }
                                    type="button"
                                    aria-pressed={
                                      selected
                                    }
                                    disabled={
                                      creating
                                    }
                                    onClick={() =>
                                      selectTemplateVersion(
                                        String(
                                          version.id
                                        )
                                      )
                                    }
                                  >

                                    <span>

                                      <strong>
                                        v{version.version}
                                      </strong>

                                      <small>
                                        {
                                          version.is_current
                                            ? "Versão atual"
                                            : "Versão anterior"
                                        }
                                      </small>

                                    </span>


                                    <span className="project-origin-robot-version">

                                      {
                                        version.is_current
                                          ? "Atual"
                                          : `v${version.version}`
                                      }

                                    </span>

                                  </button>
                                );
                              }
                            )
                        }

                      </div>
                    )
                }

              </div>

            </section>
          )
        }


        {
          selectedTemplate &&
          selectedTemplateVersion &&
          originMode ===
          "template" &&
          (
            <div
              className="project-origin-selected"
              role="status"
            >

              <Check
                size={16}
                aria-hidden="true"
              />

              <span>

                <strong>
                  Template selecionado:
                </strong>

                {" "}
                {selectedTemplate.name}
                {" · "}
                versão
                {" "}
                {selectedTemplateVersion.version}

                {
                  selectedTemplateVersion.is_current
                    ? " · Atual"
                    : " · Versão anterior"
                }

              </span>

            </div>
          )
        }


        {
          templatesError &&
          originMode ===
          "template" &&
          (
            <FeedbackBanner
              tone="error"
              title="Não foi possível carregar os Templates"
              message={templatesError}
            />
          )
        }


        {/* ====================================================
            ROBOT PUBLICADO
        ==================================================== */}

        {
          originMode ===
          "existing" &&
          (
            <section
              className="project-origin-browser"
              aria-label="Selecionar robô de origem"
            >

              <div className="project-origin-browser__folders">

                <div className="project-origin-browser__title">

                  <span>
                    Localização
                  </span>

                  <small>
                    {folders.length} pastas
                  </small>

                </div>


                <button
                  type="button"
                  className="project-folder-root"
                  aria-pressed={
                    selectedFolderId ===
                    null
                  }
                  disabled={creating}
                  onClick={() =>
                    chooseFolder(
                      null
                    )
                  }
                >

                  <Folder
                    size={15}
                    aria-hidden="true"
                  />

                  <span>
                    Raiz de Robôs
                  </span>

                </button>


                {
                  renderFolderTree(
                    null
                  )
                }

              </div>


              <div className="project-origin-browser__robots">

                <div className="project-origin-browser__title">

                  <span>
                    Robôs publicados
                  </span>

                  <small>
                    {
                      getFolderPath(
                        selectedFolderId
                      )
                    }
                  </small>

                </div>


                {
                  robotsInSelectedFolder.length ===
                  0
                    ? (
                      <div className="project-origin-browser__empty">

                        <Box
                          size={20}
                          aria-hidden="true"
                        />

                        <strong>
                          Nenhum robô nesta localização
                        </strong>

                        <span>
                          Selecione outra pasta para continuar.
                        </span>

                      </div>
                    )
                    : (
                      <div className="project-origin-robot-list">

                        {
                          robotsInSelectedFolder.map(
                            (robot) => {

                              const selected =
                                String(
                                  robot.id
                                ) ===
                                baseRobotId;


                              return (
                                <button
                                  key={
                                    robot.id
                                  }
                                  type="button"
                                  aria-pressed={
                                    selected
                                  }
                                  disabled={
                                    creating
                                  }
                                  onClick={() =>
                                    onBaseRobotChange(
                                      String(
                                        robot.id
                                      )
                                    )
                                  }
                                >

                                  <span>

                                    <strong>
                                      {robot.name}
                                    </strong>

                                    <small>
                                      Robô #{robot.id}
                                    </small>

                                  </span>


                                  <span className="project-origin-robot-version">
                                    v{robot.version}
                                  </span>

                                </button>
                              );
                            }
                          )
                        }

                      </div>
                    )
                }

              </div>

            </section>
          )
        }


        {
          selectedRobot &&
          originMode ===
          "existing" &&
          (
            <div
              className="project-origin-selected"
              role="status"
            >

              <Check
                size={16}
                aria-hidden="true"
              />

              <span>

                <strong>
                  Base selecionada:
                </strong>

                {" "}
                {
                  getFolderPath(
                    selectedRobot.folder_id
                  )
                }
                {" / "}
                {selectedRobot.name}
                {" · versão "}
                {selectedRobot.version}

              </span>

            </div>
          )
        }


        {
          robotsError &&
          originMode ===
          "existing" &&
          (
            <FeedbackBanner
              tone="error"
              title="Não foi possível carregar os robôs"
              message={robotsError}
            />
          )
        }


        {/* ====================================================
            DEMANDA
        ==================================================== */}

        <div className="project-demand-fields">

          <TextField
            id="development-project-name"
            label="Título da demanda"
            description="Use um título curto que identifique claramente o objetivo."
            type="text"
            value={projectName}
            placeholder="Ex.: Automatizar conciliação de contratos"
            required
            disabled={creating}
            onChange={
              (event) =>
                onProjectNameChange(
                  event.target.value
                )
            }
          />


          <TextAreaField
            id="development-project-description"
            label="Descrição"
            description="Opcional: registre contexto, resultado esperado ou restrições."
            value={projectDescription}
            placeholder="Descreva o que esta automação precisa resolver..."
            rows={3}
            disabled={creating}
            counter={
              `${projectDescription.length} caracteres`
            }
            onChange={
              (event) =>
                onProjectDescriptionChange(
                  event.target.value
                )
            }
          />

        </div>

      </div>


      <footer className="project-create-panel__actions">

        <p>
          {
            originMode ===
              "existing" &&
            !baseRobotId
              ? "Selecione uma versão publicada para continuar."
              : originMode ===
                  "template" &&
                !selectedTemplateVersionId
                ? "Selecione um Template para continuar."
                : !projectName.trim()
                  ? "Informe o título da demanda para continuar."
                  : "Tudo pronto para criar o workspace."
          }
        </p>


        <div>

          <Button
            variant="secondary"
            type="button"
            disabled={creating}
            onClick={onCancel}
          >
            Cancelar
          </Button>


          <Button
            variant="primary"
            type="submit"
            busy={creating}
            disabled={createDisabled}
            loadingLabel="Criando projeto"
          >
            <Plus
              size={15}
              aria-hidden="true"
            />

            {" "}
            Criar projeto
          </Button>

        </div>

      </footer>

    </form>
  );
}

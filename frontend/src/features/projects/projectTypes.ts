export type ProjectDto = {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
};

export type ProjectListDto = {
  items: ProjectDto[];
};

export const NAME_MAX = 80;
export const DESCRIPTION_MAX = 2000;

export function validateProjectFields(name: string, description: string): {
  name?: string;
  description?: string;
} {
  const errors: { name?: string; description?: string } = {};
  const trimmedName = name.trim();
  const trimmedDescription = description.trim();
  if (trimmedName.length < 1 || trimmedName.length > NAME_MAX) {
    errors.name = `Le nom doit contenir entre 1 et ${NAME_MAX} caractères.`;
  }
  if (
    trimmedDescription.length < 1 ||
    trimmedDescription.length > DESCRIPTION_MAX
  ) {
    errors.description = `La description doit contenir entre 1 et ${DESCRIPTION_MAX} caractères.`;
  }
  return errors;
}

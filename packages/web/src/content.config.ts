import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const specs = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "../../specs" }),
  schema: z.object({
    title: z.string().optional(),
    description: z.string().optional(),
  }).optional(),
});

const docs = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "../../docs" }),
  schema: z.object({
    title: z.string().optional(),
    description: z.string().optional(),
  }).optional(),
});

export const collections = { specs, docs };

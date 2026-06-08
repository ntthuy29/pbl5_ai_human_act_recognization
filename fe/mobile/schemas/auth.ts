import { z } from 'zod';

export type RegisterFormValues = {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
};

export type RegisterFormErrors = Partial<Record<keyof RegisterFormValues, string>>;

export const registerFormSchema = z
  .object({
    fullName: z.string().trim().optional().default(''),
    email: z
      .string()
      .trim()
      .min(1, 'Email không được để trống')
      .email('Email không đúng định dạng'),
    password: z
      .string()
      .min(1, 'Mật khẩu không được để trống')
      .min(8, 'Mật khẩu tối thiểu 8 ký tự'),
    confirmPassword: z.string().min(1, 'Vui lòng xác nhận mật khẩu'),
  })
  .superRefine((values, ctx) => {
    if (values.fullName && values.fullName.length > 0 && values.fullName.length < 2) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['fullName'],
        message: 'Họ và tên cần ít nhất 2 ký tự',
      });
    }

    if (values.password !== values.confirmPassword) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['confirmPassword'],
        message: 'Mật khẩu xác nhận không khớp',
      });
    }
  });

export function validateRegisterForm(values: RegisterFormValues): RegisterFormErrors {
  const result = registerFormSchema.safeParse(values);
  if (result.success) {
    return {};
  }

  const errors: RegisterFormErrors = {};
  for (const issue of result.error.issues) {
    const field = issue.path[0] as keyof RegisterFormValues | undefined;
    if (!field || errors[field]) {
      continue;
    }
    errors[field] = issue.message;
  }

  return errors;
}

/**
 * Card validators — derived from COCRDUPC COBOL business rules.
 *
 * Source: app/cbl/COCRDUPC.cbl
 * BMS map: COCRDUP
 *
 * Updatable fields per COCRDUPC:
 *   - embossed_name (CARD-EMBOSSED-NAME PIC X(50))
 *   - active_status (CARD-ACTIVE-STATUS: 'Y'/'N')
 */
import { z } from 'zod';

export const cardUpdateSchema = z.object({
  // CARD-EMBOSSED-NAME PIC X(50)
  embossed_name: z.string().max(50, 'Embossed name cannot exceed 50 characters').optional(),

  // CARD-ACTIVE-STATUS PIC X(01): 'Y' or 'N'
  active_status: z.enum(['Y', 'N'], {
    errorMap: () => ({ message: "Status must be 'Y' (active) or 'N' (inactive)" }),
  }).optional(),
});

export type CardUpdateFormValues = z.infer<typeof cardUpdateSchema>;

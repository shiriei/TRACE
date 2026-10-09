/**
 * Sticker Garden Type Definitions
 *
 * "Cute is the aesthetic. Exploration is the purpose. Stickers are the reward."
 */

export type StickerTheme = 'botanical' | 'creatures' | 'vintage' | 'humor' | 'cozy' | 'planner';

export type StickerRarity = 'common' | 'uncommon' | 'rare' | 'legendary';

export type StickerUnlockType = 'starter' | 'milestone' | 'streak' | 'manual';

export type StickerOwnershipSource = 'daily_reward' | 'milestone_reward' | 'manual_grant';

export interface StickerDefinition {
  id: string;
  name: string;
  description: string;
  theme: StickerTheme;
  rarity: StickerRarity;
  asset_path: string;
  unlock_type: StickerUnlockType;
  tags: string[];
  milestone_requirement?: Record<string, any> | null;
  is_asset_available: boolean;
}

export interface StickerPackDefinition {
  id: string;
  name: string;
  description: string;
  milestone_requirement: Record<string, any>;
  sticker_ids: string[];
}

export interface StickerOwnership {
  id: string;
  sticker_id: string;
  unlocked_at: string;
  unlock_reason: string;
  source: StickerOwnershipSource;
}

export interface OwnedSticker {
  id: string;
  sticker_id: string;
  unlocked_at: string;
  unlock_reason: string;
  source: StickerOwnershipSource;
  sticker: StickerDefinition;
}

export interface MilestoneProgress {
  id: string;
  name: string;
  streak_threshold: number;
  pack_id: string;
  is_achieved: boolean;
  is_current: boolean;
  is_locked: boolean;
  days_remaining: number;
  claimed_at?: string | null;
}

export interface StreakSummaryResponse {
  current_streak: number;
  longest_streak: number;
  total_qualifying_days: number;
  today_qualified: boolean;
  today_reward_claimed: boolean;
  today_reward_available: boolean;
  today_reward_reason?: string | null;
  next_milestone_days?: number | null;
  days_to_next_milestone?: number | null;
  total_stickers_owned: number;
  milestones: MilestoneProgress[];
}

export interface StreakEvaluationResult {
  daily_sticker_awarded?: OwnedSticker | null;
  milestones_unlocked: StickerPackDefinition[];
  streak_summary: StreakSummaryResponse;
  streak_extended?: boolean;
}


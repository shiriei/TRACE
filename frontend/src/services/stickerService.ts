/**
 * TRACE Sticker Garden Service (Frontend)
 *
 * Coordinates catalogue lookup, pack definitions, and earned sticker ownership.
 */
import {
  evaluateStreakRewards,
  fetchStickerCatalogue,
  fetchStickerPacks,
  fetchStreakSummary,
  fetchUserStickerCollection,
  grantUserSticker,
} from './api';
import {
  OwnedSticker,
  StickerDefinition,
  StickerPackDefinition,
  StickerTheme,
  StreakEvaluationResult,
  StreakSummaryResponse,
} from '../types/sticker';

class StickerService {
  /**
   * Retrieve all stickers in the catalogue, with optional theme filter.
   */
  async getCatalogue(theme?: StickerTheme): Promise<StickerDefinition[]> {
    return fetchStickerCatalogue(theme);
  }

  /**
   * Retrieve all reward pack definitions.
   */
  async getPacks(): Promise<StickerPackDefinition[]> {
    return fetchStickerPacks();
  }

  /**
   * Retrieve the user's currently earned sticker collection.
   */
  async getUserCollection(): Promise<OwnedSticker[]> {
    return fetchUserStickerCollection();
  }

  /**
   * Grant a sticker to the user's collection.
   */
  async grantSticker(
    stickerId: string,
    unlockReason: string = 'Granted to explorer collection',
    source: 'daily_reward' | 'milestone_reward' | 'manual_grant' = 'manual_grant'
  ): Promise<OwnedSticker> {
    return grantUserSticker({
      sticker_id: stickerId,
      unlock_reason: unlockReason,
      source,
    });
  }

  /**
   * Retrieve exploration streak summary derived from persisted traces.
   */
  async getStreakSummary(tzOffsetMinutes?: number): Promise<StreakSummaryResponse> {
    return fetchStreakSummary(tzOffsetMinutes);
  }

  /**
   * Safely evaluate streak rewards and claim any newly eligible rewards.
   */
  async evaluateRewards(tzOffsetMinutes?: number): Promise<StreakEvaluationResult> {
    return evaluateStreakRewards(tzOffsetMinutes);
  }
}

export const stickerService = new StickerService();

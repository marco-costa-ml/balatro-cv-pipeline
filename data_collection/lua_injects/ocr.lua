-- OCR.lua
local ocr = {}

consumable_slots = 0
joker_slots = 0
blind_display_name = ""

local HANDS = {
  "High Card","Pair","Two Pair","Three of a Kind","Straight","Flush",
  "Full House","Four of a Kind","Straight Flush","Royal Flush",
  "Five of a Kind","Flush House","Flush Five"
}

-- where to save
local SAVE_DIR = "external/ocr_dataset"

-- frame counter
ocr.frame_idx = 4980

-- switch threshold
local BLIND_REAL_LIMIT = 50

-- tiny helpers
local function q(s) return '"'..tostring(s):gsub('\\','\\\\'):gsub('"','\\"')..'"' end
local function str_or_null(v) return v and q(v) or "null" end
local function num_or_null(v) return v ~= nil and tostring(v) or "null" end

local function format_commas(n)
  local s = tostring(n)
  local sign, int = s:match("^([%-]?)(%d+)$")
  if not int then return s end
  int = int:reverse():gsub("(%d%d%d)", "%1,"):reverse():gsub("^,", "")
  return sign .. int
end

-- random ocr string
local ocr_chars = "<!? :$&(0_+-1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
local function random_ocr(len)
  local out = {}
  for i = 1, len do
    local idx = math.random(#ocr_chars)
    out[i] = ocr_chars:sub(idx, idx)
  end
  return table.concat(out)
end

-- write one json and screenshot
local function snapshot_step(idx, payload)
  local json_path = ("%s/%d.json"):format(SAVE_DIR, idx)
  local f = assert(io.open(json_path, "w"))

  local joker_count = (G.jokers and G.jokers.cards) and #G.jokers.cards or 0
  local consumable_count = (G.consumeables and G.consumeables.cards) and #G.consumeables.cards or 0

  f:write("{")
  f:write('"timestamp":', os.time(), ',')
  f:write('"frame":', idx, ',')
  f:write('"screen_filename":', q(("%d.png"):format(idx)), ',')

  f:write('"hand":{')
  f:write('"name":',  str_or_null(payload.handname), ',')
  f:write('"level":', str_or_null(payload.level), ',')
  f:write('"chips":', str_or_null(payload.chips), ',')
  f:write('"mult":',  str_or_null(payload.mult))
  f:write("},")

  local R = G.GAME and G.GAME.current_round or {}
  f:write('"state":{')
  f:write('"dollars":', num_or_null(G.GAME and G.GAME.dollars), ',')
  f:write('"hands_left":', num_or_null(R.hands_left), ',')
  f:write('"discards_left":', num_or_null(R.discards_left), ',')
  f:write('"ante":', num_or_null(G.GAME and G.GAME.round_resets and G.GAME.round_resets.ante), ',')
  f:write('"round":', num_or_null(G.GAME and G.GAME.round), ',')
  f:write('"max_jokers":', num_or_null(joker_slots), ',')
  f:write('"consumable_slots":', num_or_null(consumable_slots))
  f:write("},")

  f:write('"blind":{')
  f:write('"name":', str_or_null(blind_display_name))
  f:write("},")

  f:write('"counts":{')
  f:write('"jokers":', joker_count, ',')
  f:write('"consumables":', consumable_count)
  f:write("}")

  f:write("}")
  f:close()

  if idx > 1 then
    os.execute(('nircmd.exe savescreenshot "%s\\%d.png"'):format(SAVE_DIR, idx - 1))
  end
end

-- purge utils
local function purge_jokers()
  if G.jokers and G.jokers.cards then
    for i = #G.jokers.cards, 1, -1 do
      local c = G.jokers.cards[i]
      G.jokers:remove_card(c)
      c:remove()
    end
  end
end

local function purge_consumables()
  if G.consumeables and G.consumeables.cards then
    for i = #G.consumeables.cards, 1, -1 do
      local c = G.consumeables.cards[i]
      G.consumeables:remove_card(c)
      c:remove()
    end
  end
end

local function rand_number_str(max_len)
  local len = math.random(1, max_len or 3)
  local s = ""
  for i = 1, len do s = s .. math.random(0,9) end
  return tonumber(s)
end

function ocr.update_text(card)
  local count = 0
  local purge_next = false

  local old_set_text = Blind.set_text
  function Blind:set_text(...)
    old_set_text(self, ...)

    if not self.name or self.name == "" then return end

    if ocr.frame_idx < BLIND_REAL_LIMIT then
      self.loc_name = self.name
      blind_display_name = self.name
    else
      local s = random_ocr(math.random(4,10))
      self.loc_name = s
      blind_display_name = s
    end
  end

  local function step()
    count = count + 1

    if purge_next then
      purge_jokers()
      purge_consumables()
      purge_next = false
    end

    local name  = HANDS[math.random(#HANDS)]
    local level = rand_number_str(3)

    G.GAME.dollars = math.random(-9999, 9999)
    G.GAME.current_round.hands_left = math.random(0, 30)
    G.GAME.current_round.discards_left = math.random(0, 30)
    G.GAME.round_resets.ante = math.random(0, 40)
    G.GAME.round = math.random(0, 200)

    joker_slots = math.random(21) - 1
    consumable_slots = math.random(21) - 1

    G.GAME.max_jokers = joker_slots
    G.GAME.consumable_slots = consumable_slots

    if G.jokers and G.jokers.config then
      G.jokers.config.card_limit = joker_slots
    end
    if G.consumeables and G.consumeables.config then
      G.consumeables.config.card_limit = consumable_slots
    end

    if count % 5 == 0 and G.GAME.blind then
      G.GAME.blind:change_colour({math.random(), math.random(), math.random(), 1})
    end

    local pool = {}
    for _, b in pairs(G.P_BLINDS) do pool[#pool+1] = b end
    local blind = pool[math.random(#pool)]
    G.GAME.blind:set_blind(blind, false, false)

    for i = 1, math.random(21) - 1 do add_joker("j_joker") end
    for i = 1, math.random(21) - 1 do add_joker("c_fool") end

    local raw_chips = rand_number_str(5)
    G.GAME.chips = raw_chips
    local chips_str = format_commas(raw_chips)

    update_hand_text(
      {immediate = true, nopulse = true, delay = 0},
      {handname = name, level = level, chips = chips_str, mult = ""}
    )

    ocr.frame_idx = ocr.frame_idx + 1
    snapshot_step(ocr.frame_idx, {
      handname = name,
      level = level,
      chips = chips_str,
      mult = ""
    })

    purge_next = true

    if count < 5000 then
      G.E_MANAGER:add_event(Event{
        trigger = "before",
        delay = 6,
        func = step
      })
    end
    return true
  end

  G.E_MANAGER:add_event(Event{
    trigger = "before",
    delay = 0.1,
    func = step
  })
end

return ocr

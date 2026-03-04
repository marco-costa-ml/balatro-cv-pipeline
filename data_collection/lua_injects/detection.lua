-- detection.lua

local detection = {}

detection.joker_index = 1
detection.jokers = {
    "j_joker", "j_greedy_joker", "j_lusty_joker", "j_wrathful_joker", "j_gluttenous_joker",
    "j_jolly", "j_zany", "j_mad", "j_crazy", "j_droll", "j_sly", "j_wily", "j_clever",
    "j_devious", "j_crafty", "j_half", "j_stencil", "j_four_fingers", "j_mime", "j_credit_card",
    "j_ceremonial", "j_banner", "j_mystic_summit", "j_marble", "j_loyalty_card", "j_8_ball",
    "j_misprint", "j_dusk", "j_raised_fist", "j_chaos", "j_fibonacci", "j_steel_joker",
    "j_scary_face", "j_abstract", "j_delayed_grat", "j_hack", "j_pareidolia", "j_gros_michel",
    "j_even_steven", "j_odd_todd", "j_scholar", "j_business", "j_supernova", "j_ride_the_bus",
    "j_space", "j_egg", "j_burglar", "j_blackboard", "j_runner", "j_ice_cream", "j_dna",
    "j_splash", "j_blue_joker", "j_sixth_sense", "j_constellation", "j_hiker", "j_faceless",
    "j_green_joker", "j_superposition", "j_todo_list", "j_cavendish", "j_card_sharp", "j_red_card",
    "j_madness", "j_square", "j_seance", "j_riff_raff", "j_vampire", "j_shortcut", "j_hologram",
    "j_vagabond", "j_baron", "j_cloud_9", "j_rocket", "j_obelisk", "j_midas_mask", "j_luchador",
    "j_photograph", "j_gift", "j_turtle_bean", "j_erosion", "j_reserved_parking", "j_mail",
    "j_to_the_moon", "j_hallucination", "j_fortune_teller", "j_juggler", "j_drunkard", "j_stone",
    "j_golden", "j_lucky_cat", "j_baseball", "j_bull", "j_diet_cola", "j_trading", "j_flash",
    "j_popcorn", "j_trousers", "j_ancient", "j_ramen", "j_walkie_talkie", "j_selzer", "j_castle",
    "j_smiley", "j_campfire", "j_ticket", "j_mr_bones", "j_acrobat", "j_sock_and_buskin",
    "j_swashbuckler", "j_troubadour", "j_certificate", "j_smeared", "j_throwback",
    "j_hanging_chad", "j_rough_gem", "j_bloodstone", "j_arrowhead", "j_onyx_agate", "j_glass",
    "j_ring_master", "j_flower_pot", "j_blueprint", "j_wee", "j_merry_andy", "j_oops", "j_idol",
    "j_seeing_double", "j_matador", "j_hit_the_road", "j_duo", "j_trio", "j_family", "j_order",
    "j_tribe", "j_stuntman", "j_invisible", "j_brainstorm", "j_satellite", "j_shoot_the_moon",
    "j_drivers_license", "j_cartomancer", "j_astronomer", "j_burnt", "j_bootstraps", "j_caino",
    "j_triboulet", "j_yorick", "j_chicot", "j_perkeo"
}

detection.card_json_data = {}

-- combo config
local suits = {"Spades", "Hearts", "Diamonds", "Clubs"}
local ranks = {"2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"}
local editions = {"foil", "holo", "polychrome", false, false}
local enhancements = {"m_lucky", "m_bonus", "m_steel", "m_glass", "m_gold", "m_stone", "m_mult", "m_wild", "c_base"}
local seals = {"Blue", "Gold", "Purple", "Red", false, false}
local debuffs = {"debuffed", "facedown", false, false}

local joker_editions = {"negative", "foil", "holo", "polychrome", false, false}
local joker_stickers = {"eternal", "perishable", "rental", false}

-- generate and store all combos
detection.combos = {}
for _, s in ipairs(suits) do
    for _, r in ipairs(ranks) do
        for _, e in ipairs(editions) do
            for _, enh in ipairs(enhancements) do
                for _, seal in ipairs(seals) do
                    for _, debuff in ipairs(debuffs) do
                        table.insert(
                            detection.combos,
                            {
                                suit = s,
                                rank = r,
                                edition = e,
                                enh = enh,
                                seal = seal,
                                debuff = debuff
                            }
                        )
                    end
                end
            end
        end
    end
end

detection.joker_combos = {}
for _, joker in ipairs(detection.jokers) do
    for _, e in ipairs(joker_editions) do
        for _, sticker in ipairs(joker_stickers) do
            for _, debuff in ipairs(debuffs) do
                table.insert(
                    detection.joker_combos,
                    {
                        joker = joker,
                        edition = e,
                        debuff = debuff,
                        sticker = sticker
                    }
                )
            end
        end
    end
end

-- shuffle
math.randomseed(13444)
for i = #detection.combos, 2, -1 do
    local j = math.random(i)
    detection.combos[i], detection.combos[j] = detection.combos[j], detection.combos[i]
end

for i = #detection.joker_combos, 2, -1 do
    local j = math.random(i)
    detection.joker_combos[i], detection.joker_combos[j] = detection.joker_combos[j], detection.joker_combos[i]
end

-- combo index
local combo_index = 1
local joker_combo_index = 1

detection.spawned_ui = detection.spawned_ui or {}

function detection.set_card(card, data, offset)
    -- find matching base
    local matched_base = nil
    for _, base in pairs(G.P_CARDS) do
        if base.value == data.rank and base.suit == data.suit then
            matched_base = base
            break
        end
    end
    if matched_base then
        card:set_base(matched_base)
    else
        print("WARNING: No base card found for", data.rank, data.suit)
    end

    -- set properties
    card:set_seal(data.seal or nil, true)
    card:set_ability(G.P_CENTERS[data.enh or "c_base"], nil, true)
    if data.suit then
        card:change_suit(data.suit)
    end

    -- edition
    if data.edition then
        local edition_flags = {
            foil = false,
            holo = false,
            polychrome = false
        }

        if data.edition == "foil" then
            edition_flags.foil = true
        elseif data.edition == "holo" then
            edition_flags.holo = true
        elseif data.edition == "polychrome" then
            edition_flags.polychrome = true
        end

        card:set_edition(edition_flags, true, true)
    else
        card:set_edition(nil, true, true)
    end


    -- random back

    if data.debuff == "facedown" then
        if card.facing == "front" then
            card:flip()
        end
    else
        if card.facing == "back" then
            card:flip()
        end
    end


    if data.debuff == "debuffed" then
            card:set_debuff(true)
    end


    -- ✅ record card data into global table
    table.insert(
        detection.card_json_data,
        {
            suit = data.suit or "unknown",
            rank = data.rank or "unknown",
            edition = data.edition or "standard",
            enh = data.enh or nil,
            seal = data.seal or nil,
            debuff = data.debuff or nil,
            id = #detection.card_json_data, -- index = id
            back = nil,
            tag = nil,
            voucher = nil,
            booster = nil,
            consumable = nil,
            joker = nil,
            perishable = false,
            eternal = false,
            rental = false,
            x = offset and offset.x or nil,
            y = offset and offset.y or nil
        }
    )
end


local current_card_back = nil
function detection.screenshot_and_save_json(index)

    if type(index) ~= "number" then
        error("Expected number for index, got: " .. tostring(index))
    end

    local json_path = ("external/yolo/temp/%d.json"):format(index)
    local json_file = io.open(json_path, "w")
    json_file:write('{"filename":"', index, '.png","cards":[')

    for i, c in ipairs(detection.card_json_data) do
        local function str_or_null(val)
            return val and ('"%s"'):format(tostring(val)) or "null"
        end

        local function num_or_null(val)
            return val and string.format("%.2f", val) or "null"
        end

        local str =
            ('{"id":%s,"card_back":%s,"suit":%s,"rank":%s,"edition":%s,' ..
            '"enhancement":%s,"seal":%s,"debuff":%s,' ..
                '"x":%s,"y":%s,' ..
                    '"tag":%s,"voucher":%s,"booster":%s,"consumable":%s,"joker":%s,' ..
                        '"perishable":%s,"eternal":%s,"rental":%s}%s'):format(
            c.id or i - 1,
            str_or_null(current_card_back),
            str_or_null(c.suit),
            str_or_null(c.rank),
            str_or_null(c.edition),
            str_or_null(c.enh),
            str_or_null(c.seal),
            str_or_null(c.debuff),
            num_or_null(c.x),
            num_or_null(c.y),
            str_or_null(c.tag),
            str_or_null(c.voucher),
            str_or_null(c.booster),
            str_or_null(c.consumable),
            str_or_null(c.joker),
            tostring(c.perishable or false),
            tostring(c.eternal or false),
            tostring(c.rental or false),
            i < #detection.card_json_data and "," or ""
        )

        json_file:write(str)
    end

    json_file:write("]}")
    json_file:close()
    os.execute(('nircmd.exe savescreenshot "C:\\Users\\Marco\\Desktop\\yolo\\temp\\%d.png"'):format(index))








    detection.card_json_data = {}
end

function detection.start_image_process()
    detection.clear_spawned_ui()
    if not (G.hand and G.hand.cards) then
        return
    end
    if combo_index > #detection.combos then
        print("All combos exhausted.")
        return
    end

    --------------------------------------------------
    -- 1. capture current hand BEFORE it mutates
    --------------------------------------------------
    local hand_data = {}
    for i = 1, 8 do
        local card = G.hand.cards[i]
        local enh_key = card.config and card.config.center and card.config.center.key

        local debuff_state = false
        if card.facing == "back" then
            debuff_state = "facedown"
        elseif card.debuff then
            debuff_state = "debuffed"
        end

        hand_data[#hand_data + 1] = {
            id = i - 1,
            suit = card.base.suit,
            rank = card.base.value,
            edition = card.edition and
                (card.edition.polychrome and "polychrome" or card.edition.holo and "holo" or
                    card.edition.foil and "foil" or
                    "standard") or
                "standard",
            enh = enh_key,
            seal = card.seal,
            debuff = debuff_state
        }
    end

    --------------------------------------------------
    -- 2. dump screenshot + json (index of *prev* combo)
    --------------------------------------------------
    local snap_idx = combo_index - 8 -- first call → 0
    if snap_idx >= 0 then
        detection.screenshot_and_save_json(snap_idx)
    end


    local back_keys = {}
    for k, v in pairs(G.P_CENTERS) do
        if v.set == "Back" and v.unlocked then
            table.insert(back_keys, k)
        end
    end
    local rand_key = back_keys[math.random(#back_keys)]
    G.GAME.selected_back:change_to(G.P_CENTERS[rand_key])

    current_card_back = rand_key

    --------------------------------------------------
    -- 3. mutate hand to the NEXT combo + Spawn random ui
    --------------------------------------------------
    detection.spawn_random_ui()
    for i = 1, 8 do
        if combo_index > #detection.combos then
            break
        end
        detection.set_card(G.hand.cards[i], detection.combos[combo_index], nil)
        combo_index = combo_index + 1
    end
end

-- spawn 1-20 random ui objs + tag (tags last)
function detection.spawn_random_ui(n)
    n = n or math.random(10, 20)

    local function pulse(s)
        s:juice_up(math.random(), math.random())
        G.E_MANAGER:add_event(
            Event {
                trigger = "before",
                delay = 0.1,
                func = function()
                    if s.T then
                        pulse(s)
                    end
                    return true
                end
            }
        )
    end

    local function add_card(pool, scale)
        local list = G.P_CENTER_POOLS[pool]
        local ctr = list[math.random(#list)]
        local card = Card(0, 0, G.CARD_W * scale, G.CARD_H * scale, nil, ctr)
        if pool == "Joker" then
            card.sticker = G.sticker_map[math.random(#G.sticker_map)]
            local data = detection.joker_combos[joker_combo_index]
            ---SET JOKER EDITION
        if data.edition then
            local edition_flags = {
                foil = false,
                holo = false,
                polychrome = false,
                negative = false
            }

            if data.edition == "foil" then
                edition_flags.foil = true
            elseif data.edition == "holo" then
                edition_flags.holo = true
            elseif data.edition == "polychrome" then
                edition_flags.polychrome = true
            elseif data.edition == "negative" then
                edition_flags.negative = true
            end

            card:set_edition(edition_flags, true, true)
        else
            card:set_edition(nil, true, true)
        end


            if data.sticker == "eternal" then
                card:set_eternal(true)
                card.eternal = true
            elseif data.sticker == "perishable" then
                card:set_perishable(true)
                card.perishable = true
            end

            if data.sticker == "rental" then
                card:set_rental(true)
                card.rental = true
            end

            -- SET RANDOM DEBUFF
            if data.debuff then
                if data.debuff == "debuffed" then
                    card:set_debuff(true)
                elseif
                    data.debuff == "facedown" and
                        (data.joker == "j_photograph" or data.joker == "j_wee" or data.joker == "j_half")
                 then
                    card:flip()
                end
            end
            joker_combo_index = joker_combo_index + 1
        end

        card:start_materialize()

        -- if pool ~= "Booster" then
        --     card:set_debuff(true)
        -- end

        if pool == "Tarot" or pool == "Spectral" or pool == "Planet" then
            if math.random() > 0.8 and card.set_edition then
                local edition_flags = {negative = true}
                card:set_edition(edition_flags, true, true)
            end
        end

        local offset = detection.random_offset_outside_boxes(1)
        local box =
            UIBox {
            definition = {
                n = G.UIT.ROOT,
                config = {align = "cm", padding = 0, colour = G.C.CLEAR},
                nodes = {
                    {n = G.UIT.O, config = {object = card}}
                }
            },
            config = {
                align = "cm",
                offset = offset,
                major = G.ROOM_ATTACH
            }
        }
        detection.spawned_ui[#detection.spawned_ui + 1] = box
        local entry = {
            suit = nil,
            rank = nil,
            edition = "standard",
            enh = nil,
            seal = nil,
            debuff = data and data.debuff or nil,
            id = nil,
            back = nil,
            tag = nil,
            voucher = pool == "Voucher" and ctr.key or nil,
            booster = pool == "Booster" and ctr.key or nil,
            consumable = (pool == "Tarot" or pool == "Spectral" or pool == "Planet") and ctr.key or nil,
            joker = pool == "Joker" and (data and data.joker or ctr.key) or nil,
            perishable = card.perishable or false,
            eternal = card.eternal or false,
            rental = card.rental or false,

            x = offset.x,
            y = offset.y
        }
        
        -- handle edition detection fallback (for non-jokers, or bonus detection)
        if card.edition then
            if card.edition.polychrome then
                entry.edition = "polychrome"
            elseif card.edition.holo then
                entry.edition = "holo"
            elseif card.edition.foil then
                entry.edition = "foil"
            elseif card.edition.negative then
                entry.edition = "negative"
            end
        end

        -- if it's a card with a base (e.g., Tarot, Spectral, etc.)
        if card.base then
            entry.suit = card.base.suit
            entry.rank = card.base.value
        end

        table.insert(detection.card_json_data, entry)

        --pulse(card)
    end

    local function add_tag()
        local opts = {}
        for k, v in pairs(G.P_TAGS) do
            if v ~= G.tag_undiscovered then
                opts[#opts + 1] = k
            end
        end
        local key = opts[math.random(#opts)]
        local tag, spr = Tag(key):generate_UI()

        local offset = detection.random_offset_outside_boxes(1)
        local box =
            UIBox {
            definition = {
                n = G.UIT.ROOT,
                config = {align = "cm", padding = 0.05, colour = G.C.CLEAR},
                nodes = {tag}
            },
            config = {
                align = "cm",
                offset = offset,
                major = G.ROOM_ATTACH
            }
        }
        detection.spawned_ui[#detection.spawned_ui + 1] = box

        -- ✅ add tag to json data
        table.insert(
            detection.card_json_data,
            {
                suit = nil,
                rank = nil,
                edition = nil,
                enh = nil,
                seal = nil,
                debuff = nil,
                id = nil,
                back = nil,
                tag = key,
                voucher = nil,
                booster = nil,
                consumable = nil,
                joker = nil,
                perishable = false,
                eternal = false,
                rental = false,
                x = offset.x,
                y = offset.y
            }
        )

        --pulse(spr)
        discover_card(G.P_TAGS[key])
    end

    local pick = {
        function()
            add_card("Booster", 1.27)
        end,
        function()
            add_card("Voucher", 1)
        end,
        function()
            add_card("Tarot", 1)
        end,
        function()
            add_card("Spectral", 1)
        end,
        function()
            add_card("Planet", 1)
        end,
        function()
            add_card("Joker", 1)
        end,
        function()
            add_card("Joker", 1)
        end,
        function()
            add_card("Joker", 1)
        end,
        function()
            add_card("Joker", 1)
        end
    }

    for i = 1, n - 1 do
        pick[math.random(#pick)]()
    end
    detection.spawn_fake_ui_cards(8, 1)
    add_tag()
end

function detection.spawn_fake_ui_cards(n, scale)
    n = n or 1
    scale = scale or 1

    for i = 1, n do
        local data = detection.combos[math.random(#detection.combos)]
        if data.debuff == "facedown" then
             data.debuff = false
        end

        -- always pass valid base and center values
        local dummy_card = G.P_CARDS["c_2S"] or G.P_CARDS[1] or {} -- fallback base card
        local dummy_center = G.P_CENTERS["c_base"] or next(G.P_CENTERS)

        -- ensure params table to avoid nil derefs
        local card =
            Card(
            0,
            0,
            G.CARD_W * scale,
            G.CARD_H * scale,
            dummy_card,
            dummy_center,
            {
                viewed_back = true,
                bypass_discovery_center = true,
                bypass_discovery_ui = true,
                bypass_lock = true,
                playing_card = false
            }
        )

        -- show on screen
        local x, y
        repeat
            x = math.random() * 22 - 11
            y = math.random() * 12 - 6
        until not ((x >= -5.25 and x <= 6.8 and y <= -2.65 and y >= -9.15) or
            (x >= -7.9 and x <= -7.2 and y <= 1.6 and y >= 0.9))

        local offset = detection.random_offset_outside_boxes(1)
        local box =
            UIBox {
            definition = {
                n = G.UIT.ROOT,
                config = {align = "cm", padding = 0, colour = G.C.CLEAR},
                nodes = {
                    {n = G.UIT.O, config = {object = card}}
                }
            },
            config = {
                align = "cm",
                offset = offset,
                major = G.ROOM_ATTACH
            }
        }
        detection.spawned_ui[#detection.spawned_ui + 1] = box

        detection.set_card(card, data, offset)

        -- make it pulse
        local function pulse(s)
            s:juice_up(math.random(), math.random())
            G.E_MANAGER:add_event(
                Event {
                    trigger = "before",
                    delay = 0.1,
                    func = function()
                        if s.T then
                            pulse(s)
                        end
                        return true
                    end
                }
            )
        end
        --pulse(card)
    end
end

function detection.clear_spawned_ui()
    if detection.spawned_ui then
        for _, box in ipairs(detection.spawned_ui) do
            if box and box.remove then
                box:remove()
            end
        end
        detection.spawned_ui = {}
    end
end

function detection.random_offset_outside_boxes(min_dist)
    min_dist = (min_dist + 0.5) or 1

    local function is_inside_box(x, y, box)
        return x >= box.x1 and x <= box.x2 and y <= box.y1 and y >= box.y2
    end

    local function is_too_close(x, y)
        for _, ui in ipairs(detection.spawned_ui or {}) do
            local ox, oy = ui.config.offset.x, ui.config.offset.y
            local dx, dy = x - ox, y - oy
            if (dx * dx + dy * dy) < (min_dist * min_dist) then
                return true
            end
        end
        return false
    end

    local boxes = {
        {x1 = -5.25, y1 = 7.15, x2 = 9, y2 = 0.65},
        {x1 = -8.5, y1 = 0, x2 = -5.5, y2 = -4.5}
    }

    local x, y
    repeat
        x = math.random() * 22 - 11
        y = math.random() * 12 - 6

        local inside_any_box = false
        for _, box in ipairs(boxes) do
            if is_inside_box(x, y, box) then
                inside_any_box = true
                break
            end
        end
    until not inside_any_box and not is_too_close(x, y)

    return {x = x, y = y}
end

return detection

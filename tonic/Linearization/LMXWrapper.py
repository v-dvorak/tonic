import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Self

import smashcima as sc
from lmx.linearization.Delinearizer import Delinearizer
from lmx.linearization.Linearizer import Linearizer
from lmx.symbolic.MxlFile import MxlFile
from lmx.symbolic.part_to_score import part_to_score
from nltk.metrics import edit_distance
from smashcima import Clef, Event, Note, Score, StaffSemantic, Measure

from .Tokens import G_CLEF_ZERO_PITCH_INDEX, F_CLEF_ZERO_PITCH_INDEX
from .Tokens import (NOTE_QUARTER_TOKEN, CHORD_TOKEN, GS_CLEF_LARGE_LT,
                     BASE_TIME_BEAT_LT, STAFF_TOKEN, MEASURE_TOKEN,
                     DEFAULT_KEY_TOKEN, DEFAULT_STEM_TOKEN, PITCH_TOKENS, TIME_TOKEN, CLEF_G2_TOKEN, PITCH_ENUM)


class LMXWrapper:
    _CHORD_PITCH_GENERAL_TOKEN = "chord_pitch"
    _note_attribute_order = {
        CHORD_TOKEN: 0,
        _CHORD_PITCH_GENERAL_TOKEN: 1,
        NOTE_QUARTER_TOKEN: 2,
        DEFAULT_STEM_TOKEN: 3,
        STAFF_TOKEN: 4
    }

    def __init__(self, tokens: list[str]):
        self.tokens = tokens

    @classmethod
    def from_lmx_string(cls, score: str) -> Self:
        """
        Creates a LMXWrapper from a LMX string.

        :param score: LMX string
        :return: LMXWrapper
        """
        return LMXWrapper(score.split())

    @staticmethod
    def _mxl_to_tokens(mxl: MxlFile) -> list[str]:
        try:
            part = mxl.get_piano_part()
        except:
            part = mxl.tree.find("part")

        if part is None or part.tag != "part":
            print("No <part> element found.")
            exit()

        linearizer = Linearizer()
        linearizer.process_part(part)
        return linearizer.output_tokens

    @classmethod
    def from_musicxml_file(cls, musicxml_file: Path) -> Self:
        """
        Loads MusicXML file and returns a LMXWrapper object.

        :param musicxml_file: path to MusicXML file
        :return: LMXWrapper
        """
        with open(musicxml_file, "r") as f:
            input_xml = f.read()
            mxl = MxlFile(ET.ElementTree(
                ET.fromstring(input_xml))
            )
        return LMXWrapper(LMXWrapper._mxl_to_tokens(mxl))

    @classmethod
    def from_complex_musicxml_file(cls, musicxml_file: Path) -> Self:
        """
        Loads a complex MusicXML file and returns a simplified LMXWrapper object.

        :param musicxml_file: path to MusicXML file
        """
        return _MXMLSimplifier.complex_musicxml_file_to_lmx(musicxml_file)

    @staticmethod
    def normalized_levenstein_distance(predicted: list, ground_truth: list) -> float:
        """
        Returns the normalized Levenstein distance between the tokens
        of the predicted and ground truth LMXWrapper instances.

        The total Levenstein distance is divided by the number of tokens in ground truth.

        :param predicted: predicted LMX
        :param ground_truth: ground truth LMX
        :return: normalized Levenstein distance
        """
        return edit_distance(predicted, ground_truth) / len(ground_truth)

    def to_str(self) -> str:
        return " ".join(self.tokens)

    def __str__(self) -> str:
        return self.to_str()

    def to_musicxml(self) -> str:
        """
        Turns the LMXWrapper into a MusicXML string.
        """
        dl = Delinearizer()
        # print(self.to_str())
        dl.process_text(self.to_str())
        score_etree = part_to_score(dl.part_element)
        output_xml = str(
            ET.tostring(
                score_etree.getroot(),
                encoding="utf-8",
                xml_declaration=True
            ), "utf-8")

        return output_xml

    def canonicalize(self) -> None:
        """
        Canonicalizes the LMXWrapper instance, leaving only the necessary tokens.
        """
        dl = Delinearizer()
        dl.process_text(self.to_str())
        score_tree = part_to_score(dl.part_element)

        mxl = MxlFile(score_tree)
        self.tokens = LMXWrapper._mxl_to_tokens(mxl)

    @staticmethod
    def simplify_musicxml_file(input_path: Path, output_path: Path):
        """
        Converts given complex MusicXML file into a simplified LMX score.

        :param input_path: path to MusicXML file
        :param output_path: path to output MusicXML score
        """
        _MXMLSimplifier.simplify_musicxml_file(input_path, output_path)

    def to_reduced(
            self,
            keep_staff_token: bool = True,
            keep_measure_token: bool = True,
            keep_chord_token: bool = True,
    ) -> list[str]:
        """
        Filters out tokens that do not carry semantic information
        and leaves only pitch, staff index and measure tokens.

        :param keep_staff_token: keep staff tokens
        :param keep_measure_token: keep measure tokens
        :param keep_chord_token: keep chord tokens
        :return: list of tokens that carry semantic information
        """
        reduced = []
        staff_index_tokens_met = 0
        for token in self.tokens:
            if (
                    token in PITCH_TOKENS
                    or (keep_measure_token and token == MEASURE_TOKEN)
                    or (keep_chord_token and token == CHORD_TOKEN)
            ):
                reduced.append(token)
            elif keep_staff_token and token.startswith(STAFF_TOKEN):
                staff_index_tokens_met += 1
                if staff_index_tokens_met > 2:
                    reduced.append(token)
        return reduced

    def _to_chords(self) -> list[list[PITCH_ENUM]]:
        reduced = self.to_reduced(keep_staff_token=False, keep_measure_token=False)

        if len(reduced) == 0:
            return []

        output = []
        chord = []
        in_chord = False
        first = True
        for token in reduced:
            if token == CHORD_TOKEN:
                in_chord = True
            else:
                if in_chord:
                    # glue chord to previous tone(s)
                    chord.append(PITCH_ENUM.from_string(token, lower=False, from_name=True))
                else:
                    # reset chord
                    if first:
                        chord.append(PITCH_ENUM.from_string(token, lower=False, from_name=True))
                        first = False
                    elif len(chord) > 0:
                        output.append(chord)
                    chord = [PITCH_ENUM.from_string(token, lower=False, from_name=True)]
                in_chord = False

        # append possible leftovers
        if len(chord) > 0:
            output.append(chord)

        return output

    def _to_single_pitch_enum(self, highest: bool = True) -> list[PITCH_ENUM]:
        chords = self._to_chords()
        if highest:
            return [max(chord, key=lambda x: x.value) for chord in chords]
        else:
            return [min(chord, key=lambda x: x.value) for chord in chords]

    def to_melody(
            self,
            highest: bool = True
    ):
        """
        Returns the highest-pitch note played at a time.

        :param highest: whether to return highest or lowest pitch
        :return: list of tones
        """
        reduced = self._to_single_pitch_enum(highest=highest)

        if len(reduced) == 0:
            return []
        return [p.name for p in reduced]

    def to_contour(
            self,
            highest: bool = True,
            first: str = "*",
            up: str = "A",
            down: str = "V",
            repeat: str = "o"
    ) -> list[str]:
        reduced = self._to_single_pitch_enum(highest=highest)

        if len(reduced) == 0:
            return []
        if len(reduced) == 1:
            return [first]

        output = [first]

        for index in range(1, len(reduced)):
            if reduced[index - 1].value < reduced[index].value:
                output.append(up)
            elif reduced[index - 1].value == reduced[index].value:
                output.append(repeat)
            else:
                output.append(down)

        return output

    def to_human_readable(self, indent: int = 4) -> str:
        if len(self.tokens) == 0:
            return "No tokens found."

        # for the simplified format, minimal number of tokens is nine
        #  1 | measure
        # +1 |     key:fifths:0
        # +3 |     time beats:4 beat-type:4
        # +4 |     clef:G2 staff:1 clef:F4 staff:2
        # =9
        if len(self.tokens) > 8:
            output = ""
            indent_whitespace = indent * " "
            token_index = 0
            note_line: list[str] = []
            reset_note_line = False  # reset note construction if non-note tokens  are met
            last_note_attribute = None

            def _reset_note_constr():
                nonlocal note_line, output
                if note_line[0] == CHORD_TOKEN:
                    output += indent_whitespace + " ".join(note_line) + "\n"
                else:
                    output += indent_whitespace + (len(CHORD_TOKEN) + 1) * " " + " ".join(note_line) + "\n"
                note_line = []

            def _pad_indentation_and_new_line(tokens: list[str]) -> str:
                nonlocal indent_whitespace
                return indent_whitespace + " ".join(tokens) + "\n"

            while token_index < len(self.tokens):
                current_token = self.tokens[token_index]
                # measure separator
                if current_token == MEASURE_TOKEN:
                    output += current_token + "\n"
                    reset_note_line = True
                    token_index += 1
                # FILE HEADER
                elif current_token == DEFAULT_KEY_TOKEN:
                    output += _pad_indentation_and_new_line([current_token])
                    reset_note_line = True
                    token_index += 1
                elif current_token == TIME_TOKEN:
                    output += _pad_indentation_and_new_line([
                        current_token,  # time
                        self.tokens[token_index + 1],  # beats:4
                        self.tokens[token_index + 2]  # beat-type:4
                    ])
                    reset_note_line = True
                    token_index += 3
                elif current_token == CLEF_G2_TOKEN:
                    output += _pad_indentation_and_new_line([
                        current_token,  # clef:G2
                        self.tokens[token_index + 1],  # staff:1
                        self.tokens[token_index + 2],  # clef:F4
                        self.tokens[token_index + 3],  # staff:2
                    ])
                    reset_note_line = True
                    token_index += 4
                # NOTE LINE
                else:
                    # construct note line based in current token
                    # pitches
                    if current_token in PITCH_TOKENS:
                        attr_token = self._CHORD_PITCH_GENERAL_TOKEN
                    # "chord", "quarter", ...
                    elif current_token in [CHORD_TOKEN, NOTE_QUARTER_TOKEN, DEFAULT_STEM_TOKEN]:
                        attr_token = current_token
                    # staff
                    elif current_token.startswith(STAFF_TOKEN):
                        attr_token = STAFF_TOKEN
                    else:
                        raise ValueError(f"Invalid token \"{current_token}\"")

                    if len(note_line) > 0:
                        assert last_note_attribute is not None
                        # check the order of last and current token,
                        # note line should be reset if start of other note line is met
                        if self._note_attribute_order[attr_token] < self._note_attribute_order[last_note_attribute]:
                            _reset_note_constr()

                    note_line.append(current_token)
                    last_note_attribute = attr_token
                    token_index += 1

                if reset_note_line and len(note_line) > 0:
                    _reset_note_constr()
                reset_note_line = False

            # dump rest of constructed note line
            if len(note_line) > 0:
                _reset_note_constr()

            return output

        # invalid format
        raise ValueError(f"Invalid input sequence, to few tokens {len(self.tokens)}")


class _MXMLSimplifier:
    @staticmethod
    def _get_note_relative_pitch_to_first_staff_line(note: Note) -> int:
        event = Event.of_durable(note)
        staff_sem = StaffSemantic.of_durable(note)
        clef: Clef = event.attributes.clefs[staff_sem.staff_number]

        # get absolute position of notehead on staff
        pitch_position = clef.pitch_to_pitch_position(note.pitch) + 4
        # +4 -> smashcima indexes from the middle staff line, this project indexes from the bottom staff line

        return pitch_position

    @staticmethod
    def _note_to_lmx(note: Note) -> str:
        # get absolute position of notehead on staff
        pitch_position = _MXMLSimplifier._get_note_relative_pitch_to_first_staff_line(note)

        # get staff index grand staff
        staff_index = StaffSemantic.of_durable(note).staff_number

        # simplify note pitch: G clef at first staff, F clef at second staff
        if staff_index == 1:
            pitch_index = G_CLEF_ZERO_PITCH_INDEX + pitch_position
        elif staff_index == 2:
            pitch_index = F_CLEF_ZERO_PITCH_INDEX + pitch_position
        else:
            raise NotImplementedError(f"Unsupported staff index \"{staff_index}\"")

        return " ".join([PITCH_TOKENS[pitch_index], NOTE_QUARTER_TOKEN, DEFAULT_STEM_TOKEN,
                         f"{STAFF_TOKEN}:{staff_index}"])

    @staticmethod
    def _event_to_lmx(event: Event) -> list[str]:
        sequence: list[str] = []
        is_chord = False
        notes = [durable for durable in event.durables if isinstance(durable, Note)]
        notes: list[Note]
        notes = sorted(notes, key=lambda n: n.pitch.get_linear_pitch())
        for note in notes:
            if isinstance(note, Note):
                if is_chord:
                    sequence.append(CHORD_TOKEN)
                sequence.append(_MXMLSimplifier._note_to_lmx(note))
                is_chord = True

        return sequence

    @staticmethod
    def _sort_score_to_measures_based_on_system_breaks(score: Score) -> list[Measure]:
        """
        Splits score parts based on system breaks and puts them together into a list
        as if they were read on the physical page from left to right, top to bottom.
        """
        # Smashcima indexes from 0, "new system" measure is at the start of a new system
        # create a list of page breaks for each part -> output line by line
        assert len(score.new_system_measure_indices) > 0

        system_breaks = sorted(list(score.new_system_measure_indices))
        measures_ordered = []

        # retrieve measures from first system
        for part in score.parts:
            measures_ordered += part.measures[:system_breaks[0]]

        # retrieve middle parts
        for index in range(1, len(system_breaks)):
            start = system_breaks[index - 1]
            end = system_breaks[index]
            for part in score.parts:
                measures_ordered += part.measures[start:end]

        # TODO: investigate breaks at the end of the score
        # retrieve ends
        for part in score.parts:
            measures_ordered += part.measures[system_breaks[-1]:]

        return measures_ordered

    @staticmethod
    def smashcima_score_to_lmx(score: Score) -> LMXWrapper:
        """
        Takes Smashcima Score and turns it into LMX Event by Event.

        :param score: Smashcima Score
        :return: LMX
        """
        # assert system_breaks is None or len(score.parts) == len(system_breaks)
        sequence: list[str] = []

        sequence.append(MEASURE_TOKEN)
        sequence.append(DEFAULT_KEY_TOKEN)
        sequence.extend(BASE_TIME_BEAT_LT.split())
        sequence.extend(GS_CLEF_LARGE_LT.split())
        first = True

        # score that have only one part (one instrument) or that do not contain any page breaks
        if len(score.parts) == 0 or len(score.new_system_measure_indices) == 0:
            for part in score.parts:
                for measure in part.measures:
                    measure.sort_staves_by_number()
                    if not first:
                        sequence.append(MEASURE_TOKEN)
                    first = False
                    for event in measure.events:
                        sequence.extend(_MXMLSimplifier._event_to_lmx(event))
        # more complex scores with multiple instruments playing at the same time
        else:
            measures_ordered = _MXMLSimplifier._sort_score_to_measures_based_on_system_breaks(score)
            for measure in measures_ordered:
                measure.sort_staves_by_number()
                if not first:
                    sequence.append(MEASURE_TOKEN)
                first = False
                for event in measure.events:
                    sequence.extend(_MXMLSimplifier._event_to_lmx(event))

        return LMXWrapper(sequence)

    @staticmethod
    def complex_musicxml_file_to_lmx(file_path: Path) -> LMXWrapper:
        """
        Converts given complex MusicXML file into a simplified LMX score.

        :param file_path: path to MusicXML file
        :return: simplified LMX score
        """
        score = sc.loading.load_score(file_path)
        lmx_w = _MXMLSimplifier.smashcima_score_to_lmx(score)
        lmx_w.canonicalize()
        return lmx_w

    @staticmethod
    def simplify_musicxml_file(input_path: Path, output_path: Path):
        lmx_w = _MXMLSimplifier.complex_musicxml_file_to_lmx(input_path)
        # print(lmx_w.to_human_readable())
        output_xml = lmx_w.to_musicxml()

        with open(output_path, "w", encoding="utf8") as f:
            f.write(output_xml)
